import struct
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parsemp4 import parse_mp4_boxes
from parsemp4.boxes import FreeSpaceBox, MediaDataBox


def test_box_properties():
    free = FreeSpaceBox("free", 8, 19061, [], b"")
    assert free.properties() == {
        "size": 8,
        "box_name": "FreeSpaceBox",
        "start": 19061,
        "data": b"",
    }

    mdat = MediaDataBox("mdat", 17820776, 19069)
    assert mdat.properties() == {
        "size": 17820776,
        "box_name": "MediaDataBox",
        "start": 19069,
    }


def test_parse_free_and_mdat(tmp_path):
    mp4_path = tmp_path / "simple.mp4"
    with open(mp4_path, "wb") as f:
        # free box (size 8)
        f.write(struct.pack(">I4s", 8, b"free"))
        # mdat box (size 16, 8 bytes payload)
        f.write(struct.pack(">I4s", 16, b"mdat"))
        f.write(b"\x00" * 8)
    boxes = parse_mp4_boxes(str(mp4_path))
    assert [box.type for box in boxes] == ["free", "mdat"]
    assert isinstance(boxes[0], FreeSpaceBox)
    assert isinstance(boxes[1], MediaDataBox)
