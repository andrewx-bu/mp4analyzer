from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import struct

from .base import MP4Box


@dataclass
class MovieExtendsHeaderBox(MP4Box):
    """Movie Extends Header Box (``mehd``)."""

    version: int = 0
    flags: int = 0
    fragment_duration: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "MovieExtendsHeaderBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        if version == 1:
            fragment_duration = struct.unpack(">Q", data[4:12])[0]
        else:
            fragment_duration = struct.unpack(">I", data[4:8])[0]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            fragment_duration,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "fragment_duration": self.fragment_duration,
        }
