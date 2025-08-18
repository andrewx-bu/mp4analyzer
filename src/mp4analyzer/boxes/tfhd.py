from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import struct

from .base import MP4Box


@dataclass
class TrackFragmentHeaderBox(MP4Box):
    """Track Fragment Header Box (``tfhd``)."""

    version: int = 0
    flags: int = 0
    track_id: int = 0
    base_data_offset: int = 0
    default_sample_description_index: int = 0
    default_sample_duration: int = 0
    default_sample_size: int = 0
    default_sample_flags: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TrackFragmentHeaderBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        pos = 4
        track_id = struct.unpack(">I", data[pos : pos + 4])[0]
        pos += 4
        base_data_offset = 0
        if flags & 0x1:
            base_data_offset = struct.unpack(">Q", data[pos : pos + 8])[0]
            pos += 8
        default_sample_description_index = 0
        if flags & 0x2:
            default_sample_description_index = struct.unpack(">I", data[pos : pos + 4])[
                0
            ]
            pos += 4
        default_sample_duration = 0
        if flags & 0x8:
            default_sample_duration = struct.unpack(">I", data[pos : pos + 4])[0]
            pos += 4
        default_sample_size = 0
        if flags & 0x10:
            default_sample_size = struct.unpack(">I", data[pos : pos + 4])[0]
            pos += 4
        default_sample_flags = 0
        if flags & 0x20:
            default_sample_flags = struct.unpack(">I", data[pos : pos + 4])[0]
            pos += 4
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            track_id,
            base_data_offset,
            default_sample_description_index,
            default_sample_duration,
            default_sample_size,
            default_sample_flags,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "track_id": self.track_id,
            "base_data_offset": self.base_data_offset,
            "default_sample_description_index": self.default_sample_description_index,
            "default_sample_duration": self.default_sample_duration,
            "default_sample_size": self.default_sample_size,
            "default_sample_flags": self.default_sample_flags,
        }
