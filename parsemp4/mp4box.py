from __future__ import annotations
from dataclasses import dataclass, field
from typing import BinaryIO, List
import os
import struct


@dataclass
class MP4Box:
    """Represents an MP4 box/atom."""
    type: str
    size: int
    offset: int
    children: List["MP4Box"] = field(default_factory=list)
    data: bytes | None = None


# Common container box types that can contain child boxes
CONTAINER_BOX_TYPES = {
    "moov", "trak", "mdia", "minf", "stbl", "edts", "dinf",
    "mvex", "moof", "traf", "mfra", "udta", "meta", "ilst",
    "tref", "stsd", "sinf", "schi", "strk", "strd", "senc",
}

# Box types for which payload data should be captured
PARSED_BOX_TYPES = {"ftyp", "mvhd", "tkhd", "mdhd", "hdlr", "stsd"}


def _read_u64(f: BinaryIO) -> int:
    data = f.read(8)
    if len(data) != 8:
        raise EOFError("Unexpected end of file")
    return struct.unpack(">Q", data)[0]


def _parse_box(f: BinaryIO, file_size: int, parent_end: int | None = None) -> MP4Box | None:
    start_offset = f.tell()
    if parent_end is not None and start_offset >= parent_end:
        return None

    header = f.read(8)
    if len(header) < 8:
        return None

    size, box_type = struct.unpack(">I4s", header)
    box_type = box_type.decode("ascii")

    header_size = 8
    if size == 1:  # 64-bit extended size
        size = _read_u64(f)
        header_size = 16
    elif size == 0:
        # box extends to end of file or parent
        size = (parent_end if parent_end is not None else file_size) - start_offset

    box = MP4Box(box_type, size, start_offset)

    payload_size = size - header_size
    payload_end = start_offset + size

    if box_type in CONTAINER_BOX_TYPES and payload_size > 8:
        while f.tell() < payload_end:
            child = _parse_box(f, file_size, payload_end)
            if not child:
                break
            box.children.append(child)
    elif box_type in PARSED_BOX_TYPES and payload_size > 0:
        box.data = f.read(payload_size)
    else:
        f.seek(payload_size, os.SEEK_CUR)

    return box


def parse_mp4_boxes(file_path: str) -> List[MP4Box]:
    """Parse top-level MP4 boxes from a file."""
    file_size = os.path.getsize(file_path)
    boxes: List[MP4Box] = []
    with open(file_path, "rb") as f:
        while f.tell() < file_size:
            box = _parse_box(f, file_size)
            if not box:
                break
            boxes.append(box)
    return boxes


def format_box_tree(box: MP4Box, indent: int = 0) -> List[str]:
    """Return a list of text lines representing the box hierarchy."""
    line = f"{'  ' * indent}{box.type} (size={box.size}, offset={box.offset})"
    lines = [line]
    for child in box.children:
        lines.extend(format_box_tree(child, indent + 1))
    return lines