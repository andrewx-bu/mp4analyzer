import sys
import os
import types
import pytest

# --- Test setup: stub PyQt6 dependencies ---
fake_qimage_cls = type("QImage", (), {})
qtgui_module = types.SimpleNamespace(QImage=fake_qimage_cls)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

sys.modules.setdefault("PyQt6", types.SimpleNamespace(QtGui=qtgui_module))
sys.modules.setdefault("PyQt6.QtGui", qtgui_module)

from models import FrameData, LazyVideoFrameCollection  # noqa: E402


# --- Test fixtures ---


@pytest.fixture
def sample_collection():
    """Provide a small LazyVideoFrameCollection with 4 frames for testing."""
    timestamps = [0.0, 0.033, 0.066, 0.099]  # ~30fps
    metadata = [
        FrameData(
            size_bytes=1000, frame_type="I", timestamp=0.0, pts=0, decode_order=0
        ),
        FrameData(
            size_bytes=900, frame_type="P", timestamp=0.033, pts=1, decode_order=1
        ),
        FrameData(
            size_bytes=950, frame_type="P", timestamp=0.066, pts=2, decode_order=2
        ),
        FrameData(
            size_bytes=920, frame_type="P", timestamp=0.099, pts=3, decode_order=3
        ),
    ]
    return LazyVideoFrameCollection("", timestamps, metadata)


# --- Unit tests ---


def test_get_valid_index(sample_collection):
    """get_valid_index should clamp indices to valid range."""
    fc = sample_collection
    assert fc.get_valid_index(-5) == 0  # clamp low
    assert fc.get_valid_index(2) == 2  # valid index unchanged
    assert fc.get_valid_index(10) == fc.count - 1  # clamp high


def test_get_frame_metadata(sample_collection):
    """get_frame_metadata should return correct FrameData or None."""
    fc = sample_collection
    meta = fc.get_frame_metadata(1)
    assert meta.frame_type == "P"
    assert meta.timestamp == pytest.approx(0.033)  # floats compared safely
    assert fc.get_frame_metadata(99) is None  # out-of-range returns None


def test_clear_empties_cache(sample_collection, monkeypatch):
    """clear() should empty the internal decode cache."""
    fc = sample_collection

    # Monkeypatch _decode_gop_frames to fake decoding into cache.
    def fake_decode(self, target_index):
        self._cache[target_index] = f"frame-{target_index}"

    monkeypatch.setattr(LazyVideoFrameCollection, "_decode_gop_frames", fake_decode)

    # Access a frame to populate cache.
    fc.get_frame(0)
    assert 0 in fc._cache

    # Clear should empty cache.
    fc.clear()
    assert fc._cache == {}
