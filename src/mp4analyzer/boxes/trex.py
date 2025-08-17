from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import struct

from .base import MP4Box


@dataclass
class TrackExtendsBox(MP4Box):
    """Track Extends Box (``trex``)."""

    version: int = 0
    flags: int = 0
    track_id: int = 0
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
    ) -> "TrackExtendsBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        track_id = struct.unpack(">I", data[4:8])[0]
        default_sample_description_index = struct.unpack(">I", data[8:12])[0]
        default_sample_duration = struct.unpack(">I", data[12:16])[0]
        default_sample_size = struct.unpack(">I", data[16:20])[0]
        default_sample_flags = struct.unpack(">I", data[20:24])[0]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            track_id,
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
            "default_sample_description_index": self.default_sample_description_index,
            "default_sample_duration": self.default_sample_duration,
            "default_sample_size": self.default_sample_size,
            "default_sample_flags": self.default_sample_flags,
        }
