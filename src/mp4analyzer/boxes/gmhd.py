from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import struct
from io import BytesIO

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class GenericMediaInfoBox(MP4Box):
    """Generic Media Info Box (``gmin``)."""

    version: int = 0
    flags: int = 0
    graphics_mode: int = 0
    opcolor: Tuple[int, int, int] = (0, 0, 0)
    balance: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "GenericMediaInfoBox":
        version = data[0] if data else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        graphics_mode = struct.unpack(">H", data[4:6])[0] if len(data) >= 6 else 0
        opcolor = (
            struct.unpack(">H", data[6:8])[0] if len(data) >= 8 else 0,
            struct.unpack(">H", data[8:10])[0] if len(data) >= 10 else 0,
            struct.unpack(">H", data[10:12])[0] if len(data) >= 12 else 0,
        )
        balance = struct.unpack(">H", data[12:14])[0] if len(data) >= 14 else 0
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            graphics_mode,
            opcolor,
            balance,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "version": self.version,
                "flags": self.flags,
                "graphics_mode": self.graphics_mode,
                "opcolor": list(self.opcolor),
                "balance": self.balance,
            }
        )
        return props


@dataclass
class TextMediaHeaderBox(MP4Box):
    """Text Media Header Box (``text`` inside ``gmhd``)."""

    version: int = 0
    flags: int = 0
    display_flags: int = 0
    text_justification: int = 0
    raw: bytes | None = None

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TextMediaHeaderBox":
        version = data[0] if data else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        display_flags = struct.unpack(">I", data[4:8])[0] if len(data) >= 8 else 0
        text_justification = (
            struct.unpack(">I", data[8:12])[0] if len(data) >= 12 else 0
        )
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            display_flags,
            text_justification,
            data[12:] if len(data) > 12 else None,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "version": self.version,
                "flags": self.flags,
                "display_flags": self.display_flags,
                "text_justification": self.text_justification,
            }
        )
        if self.raw:
            props["data"] = bytes_to_hex(self.raw)
        return props


@dataclass
class GenericMediaHeaderBox(MP4Box):
    """Generic Media Header Box (``gmhd``)."""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "GenericMediaHeaderBox":
        stream = BytesIO(data)
        parsed_children: List[MP4Box] = []
        pos = 0
        while pos + 8 <= len(data):
            header = stream.read(8)
            if len(header) < 8:
                break
            child_size, child_type = struct.unpack(">I4s", header)
            if child_size < 8 or pos + child_size > len(data):
                break
            payload = stream.read(child_size - 8)
            child_type_str = child_type.decode("ascii")
            child_offset = offset + 8 + pos
            if child_type_str == "gmin":
                child = GenericMediaInfoBox.from_parsed(
                    child_type_str, child_size, child_offset, payload, []
                )
            elif child_type_str == "text":
                child = TextMediaHeaderBox.from_parsed(
                    child_type_str, child_size, child_offset, payload, []
                )
            else:
                child = MP4Box(child_type_str, child_size, child_offset, [], payload)
            parsed_children.append(child)
            pos += child_size
            stream.seek(pos)
        return cls(box_type, size, offset, parsed_children, None)

    def properties(self) -> Dict[str, object]:
        return super().properties()
