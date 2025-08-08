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


@dataclass
class MovieHeaderBox(MP4Box):
    """Movie Header Box (``mvhd``)."""

    version: int = 0
    flags: int = 0
    timescale: int = 0
    duration: int = 0
    creation_time: int = 0
    modification_time: int = 0
    rate: int = 0
    volume: float = 0.0
    matrix: List[int] = field(default_factory=list)
    next_track_id: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "MovieHeaderBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        pos = 4
        if version == 1:
            creation_time = struct.unpack(">Q", data[pos : pos + 8])[0]
            modification_time = struct.unpack(">Q", data[pos + 8 : pos + 16])[0]
            timescale = struct.unpack(">I", data[pos + 16 : pos + 20])[0]
            duration = struct.unpack(">Q", data[pos + 20 : pos + 28])[0]
            pos += 28
        else:
            creation_time = struct.unpack(">I", data[pos : pos + 4])[0]
            modification_time = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
            timescale = struct.unpack(">I", data[pos + 8 : pos + 12])[0]
            duration = struct.unpack(">I", data[pos + 12 : pos + 16])[0]
            pos += 16
        rate = struct.unpack(">I", data[pos : pos + 4])[0]
        volume = struct.unpack(">H", data[pos + 4 : pos + 6])[0] / 256
        pos += 6
        pos += 10  # reserved
        matrix = [
            struct.unpack(">I", data[pos + i * 4 : pos + (i + 1) * 4])[0]
            for i in range(9)
        ]
        pos += 36
        pos += 24  # pre-defined
        next_track_id = struct.unpack(">I", data[pos : pos + 4])[0]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            timescale,
            duration,
            creation_time,
            modification_time,
            rate,
            volume,
            matrix,
            next_track_id,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "creation_time": self.creation_time,
            "modification_time": self.modification_time,
            "timescale": self.timescale,
            "duration": self.duration,
            "rate": self.rate,
            "volume": self.volume,
            "matrix": self.matrix,
            "next_track_id": self.next_track_id,
        }


@dataclass
class TrackHeaderBox(MP4Box):
    """Track Header Box (``tkhd``)."""

    version: int = 0
    track_id: int = 0
    duration: int = 0
    width: float = 0.0
    height: float = 0.0
    creation_time: int = 0
    modification_time: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "TrackHeaderBox":
        version = data[0]
        if version == 1:
            creation_time = struct.unpack(">Q", data[4:12])[0]
            modification_time = struct.unpack(">Q", data[12:20])[0]
            track_id = struct.unpack(">I", data[20:24])[0]
            duration = struct.unpack(">Q", data[28:36])[0]
            width = struct.unpack(">I", data[88:92])[0] / 65536
            height = struct.unpack(">I", data[92:96])[0] / 65536
        else:
            creation_time = struct.unpack(">I", data[4:8])[0]
            modification_time = struct.unpack(">I", data[8:12])[0]
            track_id = struct.unpack(">I", data[12:16])[0]
            duration = struct.unpack(">I", data[20:24])[0]
            width = struct.unpack(">I", data[76:80])[0] / 65536
            height = struct.unpack(">I", data[80:84])[0] / 65536
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            track_id,
            duration,
            width,
            height,
            creation_time,
            modification_time,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "version": self.version,
                "track_id": self.track_id,
                "duration": self.duration,
                "width": self.width,
                "height": self.height,
            }
        )
        return props


@dataclass
class ObjectDescriptorBox(MP4Box):
    """Object Descriptor Box (``iods``)."""

    version: int = 0
    flags: int = 0
    descriptor: bytes = b""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "ObjectDescriptorBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        descriptor = data[4:]
        return cls(box_type, size, offset, children or [], None, version, flags, descriptor)

    def properties(self) -> Dict[str, object]:
        hexstr = self.descriptor.hex()
        grouped = " ".join(hexstr[i:i + 8] for i in range(0, len(hexstr), 8))
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "data": grouped,
        }

# Common container box types that can contain child boxes
CONTAINER_BOX_TYPES = {
    "moov",
    "trak",
    "mdia",
    "minf",
    "stbl",
    "edts",
    "dinf",
    "mvex",
    "moof",
    "traf",
    "mfra",
    "udta",
    "meta",
    "ilst",
    "tref",
    "stsd",
    "sinf",
    "schi",
    "strk",
    "strd",
    "senc",
}

# Mapping of box type to specialised box class
BOX_PARSERS: Dict[str, Type[MP4Box]] = {
    "ftyp": FileTypeBox,
    "mvhd": MovieHeaderBox,
    "tkhd": TrackHeaderBox,
    "iods": ObjectDescriptorBox,
}

# Box types for which raw payload data should be captured for later processing
RAW_DATA_BOX_TYPES = {"mdhd", "hdlr", "stsd"}

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