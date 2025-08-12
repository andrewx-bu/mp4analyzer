import sys
import types

# Stub QImage to avoid PyQt6 dependency
fake_qimage_cls = type("QImage", (), {})
qtgui_module = types.SimpleNamespace(QImage=fake_qimage_cls)
sys.modules.setdefault("PyQt6", types.SimpleNamespace(QtGui=qtgui_module))
sys.modules.setdefault("PyQt6.QtGui", qtgui_module)

from models import VideoMetadata, FrameData, LazyVideoFrameCollection  # noqa: E402


def _build_collection(frame_types):
    timestamps = [i * 0.033 for i in range(len(frame_types))]
    metadata = [
        FrameData(
            size_bytes=1000,
            frame_type=ft,
            timestamp=timestamps[i],
            pts=i,
            decode_order=i,
        )
        for i, ft in enumerate(frame_types)
    ]
    return LazyVideoFrameCollection("", timestamps, metadata)


def test_video_metadata_properties():
    meta = VideoMetadata("f.mp4", 1.23, 640, 480, "h264", 100, 30.0)
    assert meta.resolution_text == "640x480"
    assert meta.duration_text == "1.23s"


def test_frame_data_is_keyframe():
    assert FrameData(0, "I", 0.0, 0, 0).is_keyframe
    assert not FrameData(0, "P", 0.0, 0, 0).is_keyframe


def test_find_gop_boundaries():
    fc = _build_collection(["I", "P", "P", "P", "I", "P"])
    assert fc._find_gop_start(3) == 0
    assert fc._find_gop_end(0) == 3
    assert fc._find_gop_start(4) == 4
    assert fc._find_gop_end(4) == 5


def test_decode_gop_frames_small(monkeypatch):
    fc = _build_collection(["I", "P", "P", "P"])
    called = {}

    def fake_range(start, end):
        called["start"] = start
        called["end"] = end

    monkeypatch.setattr(fc, "_decode_frame_range", fake_range)
    fc._decode_gop_frames(2)
    assert called == {"start": 0, "end": 3}


def test_decode_gop_frames_large(monkeypatch):
    frame_types = ["I"] + ["P"] * 29
    fc = _build_collection(frame_types)
    called = {}

    def fake_range(start, end):
        called["start"] = start
        called["end"] = end

    monkeypatch.setattr(fc, "_decode_frame_range", fake_range)
    fc._decode_gop_frames(15)
    assert called == {"start": 5, "end": 25}


def test_decode_gop_frames_skips_when_cached(monkeypatch):
    fc = _build_collection(["I", "P", "P", "P"])
    for i in range(4):
        fc._cache[i] = object()

    def fake_range(start, end):
        raise AssertionError("_decode_frame_range should not be called")

    monkeypatch.setattr(fc, "_decode_frame_range", fake_range)
    fc._decode_gop_frames(1)
