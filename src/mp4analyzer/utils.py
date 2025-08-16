from typing import List
from .boxes import MP4Box


def format_box_tree(box: MP4Box, indent: int = 0) -> List[str]:
    """Return a list of text lines representing the box hierarchy."""
    line = f"{'  ' * indent}{box.type} (size={box.size}, offset={box.offset})"
    lines = [line]
    for child in box.children:
        lines.extend(format_box_tree(child, indent + 1))
    return lines


def bytes_to_hex(data: bytes | None) -> str:
    """Return a spaced hexadecimal representation of *data*.

    Groups bytes into 4-byte (8 hex char) chunks separated by spaces for
    readability. Returns an empty string if *data* is falsy.
    """
    if not data:
        return ""
    hexstr = data.hex()
    return " ".join(hexstr[i : i + 8] for i in range(0, len(hexstr), 8))
