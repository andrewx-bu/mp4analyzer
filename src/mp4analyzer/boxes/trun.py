from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict
import struct

from .base import MP4Box


@dataclass
class TrackRunBox(MP4Box):
    """Track Run Box (``trun``)."""

    version: int = 0
    flags: int = 0
    sample_count: int = 0
    data_offset: int = 0
    first_sample_flags: int = 0
    sample_duration: List[int] = field(default_factory=list)
    sample_size: List[int] = field(default_factory=list)
    sample_flags: List[int] = field(default_factory=list)
    sample_composition_time_offset: List[int] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TrackRunBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        pos = 4
        sample_count = struct.unpack(">I", data[pos : pos + 4])[0]
        pos += 4
        data_offset = 0
        if flags & 0x1:
            data_offset = struct.unpack(">i", data[pos : pos + 4])[0]
            pos += 4
        first_sample_flags = 0
        if flags & 0x4:
            first_sample_flags = struct.unpack(">I", data[pos : pos + 4])[0]
            pos += 4
        sample_duration: List[int] = []
        sample_size: List[int] = []
        sample_flags: List[int] = []
        sample_composition_time_offset: List[int] = []
        for _ in range(sample_count):
            if flags & 0x100:
                sample_duration.append(struct.unpack(">I", data[pos : pos + 4])[0])
                pos += 4
            if flags & 0x200:
                sample_size.append(struct.unpack(">I", data[pos : pos + 4])[0])
                pos += 4
            if flags & 0x400:
                sample_flags.append(struct.unpack(">I", data[pos : pos + 4])[0])
                pos += 4
            if flags & 0x800:
                if version == 0:
                    val = struct.unpack(">I", data[pos : pos + 4])[0]
                else:
                    val = struct.unpack(">i", data[pos : pos + 4])[0]
                sample_composition_time_offset.append(val)
                pos += 4
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            sample_count,
            data_offset,
            first_sample_flags,
            sample_duration,
            sample_size,
            sample_flags,
            sample_composition_time_offset,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "sample_duration": self.sample_duration,
            "sample_size": self.sample_size,
            "sample_flags": self.sample_flags,
            "sample_composition_time_offset": self.sample_composition_time_offset,
            "start": self.offset,
            "sample_count": self.sample_count,
            "data_offset": self.data_offset,
            "first_sample_flags": self.first_sample_flags,
        }
