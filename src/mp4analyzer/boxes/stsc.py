from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class SampleToChunkBox(MP4Box):
    """Sample To Chunk Box (``stsc``)."""

    version: int = 0
    flags: int = 0
    first_chunk: List[int] | None = None
    samples_per_chunk: List[int] | None = None
    sample_description_index: List[int] | None = None

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SampleToChunkBox":
        version = data[0] if len(data) > 0 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        entry_count = struct.unpack(">I", data[4:8])[0] if len(data) >= 8 else 0
        first_chunk: List[int] = []
        samples_per_chunk: List[int] = []
        sample_description_index: List[int] = []
        pos = 8
        for _ in range(entry_count):
            if pos + 12 > len(data):
                break
            first_chunk.append(struct.unpack(">I", data[pos : pos + 4])[0])
            samples_per_chunk.append(struct.unpack(">I", data[pos + 4 : pos + 8])[0])
            sample_description_index.append(
                struct.unpack(">I", data[pos + 8 : pos + 12])[0]
            )
            pos += 12
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            first_chunk,
            samples_per_chunk,
            sample_description_index,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "first_chunk": self.first_chunk,
            "samples_per_chunk": self.samples_per_chunk,
            "sample_description_index": self.sample_description_index,
        }
