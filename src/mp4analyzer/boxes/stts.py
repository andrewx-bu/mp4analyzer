from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class TimeToSampleBox(MP4Box):
    """Decoding Time to Sample Box (``stts``)."""

    version: int = 0
    flags: int = 0
    sample_counts: List[int] = None
    sample_deltas: List[int] = None

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TimeToSampleBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        entry_count = struct.unpack(">I", data[4:8])[0]
        sample_counts: List[int] = []
        sample_deltas: List[int] = []
        pos = 8
        for _ in range(entry_count):
            if pos + 8 > len(data):
                break
            count = struct.unpack(">I", data[pos : pos + 4])[0]
            delta = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
            sample_counts.append(count)
            sample_deltas.append(delta)
            pos += 8
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            sample_counts,
            sample_deltas,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "sample_counts": self.sample_counts,
            "sample_deltas": self.sample_deltas,
        }
