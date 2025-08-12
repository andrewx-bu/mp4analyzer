from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class MediaHeaderBox(MP4Box):
    """Media Header Box (``mdhd``)."""

    version: int = 0
    flags: int = 0
    creation_time: int = 0
    modification_time: int = 0
    timescale: int = 0
    duration: int = 0
    language: int = 0
    languageString: str = ""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "MediaHeaderBox":
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
        language = struct.unpack(">H", data[pos : pos + 2])[0]
        pos += 2
        # skip pre_defined
        pos += 2
        lang_code = language & 0x7FFF
        language_str = "".join(
            chr(((lang_code >> shift) & 0x1F) + 0x60) for shift in (10, 5, 0)
        )
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            creation_time,
            modification_time,
            timescale,
            duration,
            language,
            language_str,
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
            "language": self.language,
            "languageString": self.languageString,
        }
