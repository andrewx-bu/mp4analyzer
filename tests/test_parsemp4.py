import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parsemp4 import parse_mp4_boxes
from parsemp4.utils import format_box_tree


@pytest.mark.skipif(
    not Path("tests/fixtures/sample.mp4").exists(),
    reason="sample MP4 file not available",
)
def test_parse_mp4_boxes_sample():
    path = os.path.join("tests", "fixtures", "sample.mp4")
    boxes = parse_mp4_boxes(path)
    types = [box.type for box in boxes]
    assert types == ["ftyp", "moov", "mdat"]
    tree_lines = []
    for box in boxes:
        tree_lines.extend(format_box_tree(box))
    assert tree_lines == [
        "ftyp (size=20, offset=0)",
        "moov (size=8, offset=20)",
        "mdat (size=8, offset=28)",
    ]
