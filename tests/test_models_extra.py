import sys
import types

# --- Test setup: stub PyQt6 dependencies ---
fake_qimage_cls = type("QImage", (), {})
qtgui_module = types.SimpleNamespace(QImage=fake_qimage_cls)
sys.modules.setdefault("PyQt6", types.SimpleNamespace(QtGui=qtgui_module))
sys.modules.setdefault("PyQt6.QtGui", qtgui_module)

from models import VideoMetadata, FrameData, LazyVideoFrameCollection  # noqa: E402


# --- Helper to construct collections for tests ---


def _build_collection(frame_types):
    """Build a LazyVideoFrameCollection with given frame types (I/P)."""
    timestamps = [i * 0.033 for i in range(len(frame_types))]  # ~30fps
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


# --- Unit tests ---


def test_video_metadata_properties():
    """VideoMetadata should return formatted resolution and duration."""
    meta = VideoMetadata("f.mp4", 1.23, 640, 480, "h264", 100, 30.0)
    assert meta.resolution_text == "640x480"
    assert meta.duration_text == "1.23s"


def test_frame_data_is_keyframe():
    """FrameData.is_keyframe should be True only for I-frames."""
    assert FrameData(0, "I", 0.0, 0, 0).is_keyframe
    assert not FrameData(0, "P", 0.0, 0, 0).is_keyframe


def test_find_gop_boundaries():
    """_find_gop_start/_find_gop_end should locate correct GOP boundaries."""
    fc = _build_collection(["I", "P", "P", "P", "I", "P"])
    assert fc._find_gop_start(3) == 0  # index 3 belongs to first GOP
    assert fc._find_gop_end(0) == 3  # GOP from 0 → 3
    assert fc._find_gop_start(4) == 4  # second GOP starts at 4
    assert fc._find_gop_end(4) == 5  # GOP from 4 → 5


def test_decode_gop_frames_small(monkeypatch):
    """_decode_gop_frames should decode the full small GOP around target index."""
    fc = _build_collection(["I", "P", "P", "P"])
    called = {}

    def fake_range(start, end):
        # Record start/end values for verification
        called["start"] = start
        called["end"] = end

    monkeypatch.setattr(fc, "_decode_frame_range", fake_range)
    fc._decode_gop_frames(2)  # target is inside first GOP
    assert called == {"start": 0, "end": 3}


def test_decode_gop_frames_large(monkeypatch):
    """_decode_gop_frames should decode a windowed GOP if too large."""
    frame_types = ["I"] + ["P"] * 29  # GOP of 30 frames
    fc = _build_collection(frame_types)
    called = {}

    def fake_range(start, end):
        called["start"] = start
        called["end"] = end

    monkeypatch.setattr(fc, "_decode_frame_range", fake_range)
    fc._decode_gop_frames(15)  # middle of large GOP
    assert called == {"start": 5, "end": 25}  # narrowed window


def test_decode_gop_frames_skips_when_cached(monkeypatch):
    """_decode_gop_frames should skip decoding if all frames are already cached."""
    fc = _build_collection(["I", "P", "P", "P"])
    # Pretend all frames are already cached
    for i in range(4):
        fc._cache[i] = object()

    def fake_range(start, end):
        raise AssertionError("_decode_frame_range should not be called")

    monkeypatch.setattr(fc, "_decode_frame_range", fake_range)
    fc._decode_gop_frames(1)  # no-op since cache is full
