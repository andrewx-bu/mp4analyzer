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

from video_loader import extract_metadata


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
