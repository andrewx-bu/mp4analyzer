from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class SampleSizeBox(MP4Box):
    """Sample Size Box (``stsz``)."""

    version: int = 0
    flags: int = 0
    sample_sizes: List[int] | None = None
    sample_size: int = 0
    sample_count: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SampleSizeBox":
        version = data[0] if len(data) > 0 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        sample_size = struct.unpack(">I", data[4:8])[0] if len(data) >= 8 else 0
        sample_count = struct.unpack(">I", data[8:12])[0] if len(data) >= 12 else 0
        sample_sizes: List[int] = []
        if sample_size == 0:
            pos = 12
            for _ in range(sample_count):
                if pos + 4 > len(data):
                    break
                sample_sizes.append(struct.unpack(">I", data[pos : pos + 4])[0])
                pos += 4
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            sample_sizes,
            sample_size,
            sample_count,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "sample_sizes": self.sample_sizes,
            "sample_size": self.sample_size,
            "sample_count": self.sample_count,
        }
