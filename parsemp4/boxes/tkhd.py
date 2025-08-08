from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import struct
from .base import MP4Box


@dataclass
class TrackHeaderBox(MP4Box):
    """Track Header Box (``tkhd``)."""

    version: int = 0
    track_id: int = 0
    duration: int = 0
    width: float = 0.0
    height: float = 0.0
    creation_time: int = 0
    modification_time: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "TrackHeaderBox":
        version = data[0]
        if version == 1:
            creation_time = struct.unpack(">Q", data[4:12])[0]
            modification_time = struct.unpack(">Q", data[12:20])[0]
            track_id = struct.unpack(">I", data[20:24])[0]
            duration = struct.unpack(">Q", data[28:36])[0]
            width = struct.unpack(">I", data[88:92])[0] / 65536
            height = struct.unpack(">I", data[92:96])[0] / 65536
        else:
            creation_time = struct.unpack(">I", data[4:8])[0]
            modification_time = struct.unpack(">I", data[8:12])[0]
            track_id = struct.unpack(">I", data[12:16])[0]
            duration = struct.unpack(">I", data[20:24])[0]
            width = struct.unpack(">I", data[76:80])[0] / 65536
            height = struct.unpack(">I", data[80:84])[0] / 65536
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            track_id,
            duration,
            width,
            height,
            creation_time,
            modification_time,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "version": self.version,
                "track_id": self.track_id,
                "duration": self.duration,
                "width": self.width,
                "height": self.height,
            }
        )
        return props