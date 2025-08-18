from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import struct

from .base import MP4Box


@dataclass
class MovieFragmentHeaderBox(MP4Box):
    """Movie Fragment Header Box (``mfhd``)."""

    version: int = 0
    flags: int = 0
    sequence_number: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "MovieFragmentHeaderBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        sequence_number = struct.unpack(">I", data[4:8])[0]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            sequence_number,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "sequence_number": self.sequence_number,
        }
