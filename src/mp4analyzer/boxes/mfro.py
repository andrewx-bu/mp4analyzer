from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import struct

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class MovieFragmentRandomAccessOffsetBox(MP4Box):
    """Movie Fragment Random Access Offset Box (``mfro``)."""

    version: int = 0
    flags: int = 0
    mfra_size: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "MovieFragmentRandomAccessOffsetBox":
        version = data[0] if len(data) > 0 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        mfra_size = struct.unpack(">I", data[4:8])[0] if len(data) >= 8 else 0
        return cls(
            box_type, size, offset, children or [], data, version, flags, mfra_size
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "data": bytes_to_hex(self.data[4:] if self.data else b""),
            "mfra_size": self.mfra_size,
        }
