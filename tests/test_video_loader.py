import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure the project root is on the Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Provide dummy PyQt6 modules to satisfy imports in models
pyqt6 = types.ModuleType("PyQt6")
qtgui = types.ModuleType("PyQt6.QtGui")
qtgui.QImage = type("QImage", (), {})
pyqt6.QtGui = qtgui
sys.modules.setdefault("PyQt6", pyqt6)
sys.modules.setdefault("PyQt6.QtGui", qtgui)

from video_loader import (  # noqa: E402
    extract_metadata,
    check_ffmpeg,
    VideoLoader,
    VideoLoaderError,
)
from models import VideoMetadata, FrameData  # noqa: E402


def test_extract_metadata_success():
    ffprobe_output = json.dumps(
        {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30000/1001",
                    "nb_frames": "1000",
                    "duration": "33.366",
                }
            ],
            "format": {"duration": "33.366"},
        }
    )
    mock_completed = MagicMock(stdout=ffprobe_output, returncode=0)
    with patch("video_loader.subprocess.run", return_value=mock_completed):
        metadata = extract_metadata("dummy.mp4")

    assert metadata is not None
    assert metadata.duration_seconds == pytest.approx(33.366)
    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.codec_name == "h264"
    assert metadata.total_frames == 1000
    assert metadata.frames_per_second == pytest.approx(30000 / 1001)


def test_extract_metadata_failure():
    mock_completed = MagicMock(stdout="", returncode=1)
    with patch("video_loader.subprocess.run", return_value=mock_completed):
        metadata = extract_metadata("dummy.mp4")
    assert metadata is None


def test_check_ffmpeg(monkeypatch):
    monkeypatch.setattr("video_loader._run_ffmpeg_cmd", lambda cmd: "v")
    assert check_ffmpeg() == (True, True)


def test_check_ffmpeg_partial(monkeypatch):
    def fake(cmd):
        return "v" if cmd[0] == "ffmpeg" else None

    monkeypatch.setattr("video_loader._run_ffmpeg_cmd", fake)
    assert check_ffmpeg() == (True, False)


def test_videoloader_init_failure(monkeypatch):
    monkeypatch.setattr("video_loader.check_ffmpeg", lambda: (False, True))
    with pytest.raises(VideoLoaderError):
        VideoLoader()
    monkeypatch.setattr("video_loader.check_ffmpeg", lambda: (True, False))
    with pytest.raises(VideoLoaderError):
        VideoLoader()


def test_videoloader_load_video_file(monkeypatch):
    meta = VideoMetadata("f", 1.0, 100, 100, "h264", 10, 30.0)
    frames = [FrameData(0, "I", 0.0, 0, 0)]
    timestamps = [0.0]

    monkeypatch.setattr(
        "video_loader.parse_frames", lambda path: (meta, frames, timestamps)
    )
    monkeypatch.setattr("video_loader.check_ffmpeg", lambda: (True, True))
    loader = VideoLoader()
    logs = []
    out_meta, collection = loader.load_video_file("dummy.mp4", log_callback=logs.append)
    assert out_meta == meta
    assert collection.count == 1
    assert any("Using FFmpeg" in msg for msg in logs)
