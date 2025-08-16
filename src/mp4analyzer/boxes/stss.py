from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class SyncSampleBox(MP4Box):
    """Sync Sample Box (``stss``)."""

    version: int = 0
    flags: int = 0
    sample_numbers: List[int] | None = None

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SyncSampleBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        entry_count = struct.unpack(">I", data[4:8])[0] if len(data) >= 8 else 0
        sample_numbers: List[int] = []
        pos = 8
        for _ in range(entry_count):
            if pos + 4 > len(data):
                break
            sample_numbers.append(struct.unpack(">I", data[pos : pos + 4])[0])
            pos += 4
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            sample_numbers,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "sample_numbers": self.sample_numbers,
        }
