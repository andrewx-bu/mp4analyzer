from __future__ import annotations
from dataclasses import dataclass, field
from typing import BinaryIO, List, Dict, Type
import os
import struct


@dataclass
class MP4Box:
    """Represents a generic MP4 box/atom."""
    type: str
    size: int
    offset: int
    children: List["MP4Box"] = field(default_factory=list)
    # Raw payload data for boxes that are not fully parsed yet.  This
    # allows other parts of the application to extract information
    # until dedicated box classes are implemented.
    data: bytes | None = None

    def properties(self) -> Dict[str, object]:
        """Return a dictionary of properties for UI display."""
        return {
            "size": self.size,
            "box_name": self.__class__.__name__,
            "start": self.offset,
        }

@dataclass
class FileTypeBox(MP4Box):
    """The mandatory File Type Box (``ftyp``)."""

    major_brand: str = ""
    minor_version: int = 0
    compatible_brands: List[str] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "FileTypeBox":
        major_brand = data[0:4].decode("ascii")
        minor_version = struct.unpack(">I", data[4:8])[0]
        compat = [
            data[i : i + 4].decode("ascii")
            for i in range(8, len(data), 4)
            if len(data[i : i + 4]) == 4
        ]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            major_brand,
            minor_version,
            compat,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "major_brand": self.major_brand,
                "minor_version": self.minor_version,
                "compatible_brands": self.compatible_brands,
            }
        )
        return props

# Common container box types that can contain child boxes
CONTAINER_BOX_TYPES = {
    "moov", "trak", "mdia", "minf", "stbl", "edts", "dinf",
    "mvex", "moof", "traf", "mfra", "udta", "meta", "ilst",
    "tref", "stsd", "sinf", "schi", "strk", "strd", "senc",
}

# Mapping of box type to specialised box class
BOX_PARSERS: Dict[str, Type[MP4Box]] = {
    "ftyp": FileTypeBox,
}

# Box types for which raw payload data should be captured for later processing
RAW_DATA_BOX_TYPES = {"mvhd", "tkhd", "mdhd", "hdlr", "stsd"}

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

    payload_size = size - header_size
    payload_end = start_offset + size

    children: List[MP4Box] = []
    data: bytes | None = None

    if box_type in CONTAINER_BOX_TYPES and payload_size > 8:
        while f.tell() < payload_end:
            child = _parse_box(f, file_size, payload_end)
            if not child:
                break
            children.append(child)
    else:
        if payload_size > 0 and (box_type in BOX_PARSERS or box_type in RAW_DATA_BOX_TYPES):
            data = f.read(payload_size)
        else:
            f.seek(payload_size, os.SEEK_CUR)

    box_cls = BOX_PARSERS.get(box_type)
    if box_cls:
        # For parsed boxes we expect data to be present
        parsed_box = box_cls.from_parsed(box_type, size, start_offset, data or b"", children)
        return parsed_box

    return MP4Box(box_type, size, start_offset, children, data)


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