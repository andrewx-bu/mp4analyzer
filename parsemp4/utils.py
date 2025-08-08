from typing import List
from .boxes import MP4Box


def format_box_tree(box: MP4Box, indent: int = 0) -> List[str]:
    """Return a list of text lines representing the box hierarchy."""
    line = f"{'  ' * indent}{box.type} (size={box.size}, offset={box.offset})"
    lines = [line]
    for child in box.children:
        lines.extend(format_box_tree(child, indent + 1))
    return lines
