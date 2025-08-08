from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
import struct
from .base import MP4Box


@dataclass
class TrackHeaderBox(MP4Box):
    """Track Header Box (``tkhd``)."""

    version: int = 0
    flags: int = 0
    track_id: int = 0
    duration: int = 0
    width: int = 0
    height: int = 0
    creation_time: int = 0
    modification_time: int = 0
    layer: int = 0
    alternate_group: int = 0
    volume: float = 0.0
    matrix: List[int] = field(default_factory=list)

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
        flags = int.from_bytes(data[1:4], "big")
        pos = 4

        if version == 1:
            creation_time = struct.unpack(">Q", data[pos : pos + 8])[0]
            modification_time = struct.unpack(">Q", data[pos + 8 : pos + 16])[0]
            track_id = struct.unpack(">I", data[pos + 16 : pos + 20])[0]
            pos += 24  # skip reserved
            duration = struct.unpack(">Q", data[pos : pos + 8])[0]
            pos += 8
        else:
            creation_time = struct.unpack(">I", data[pos : pos + 4])[0]
            modification_time = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
            track_id = struct.unpack(">I", data[pos + 8 : pos + 12])[0]
            pos += 16  # skip reserved
            duration = struct.unpack(">I", data[pos : pos + 4])[0]
            pos += 4

        pos += 8  # skip reserved
        layer = struct.unpack(">h", data[pos : pos + 2])[0]
        alternate_group = struct.unpack(">h", data[pos + 2 : pos + 4])[0]
        volume = struct.unpack(">H", data[pos + 4 : pos + 6])[0] / 256
        pos += 6
        pos += 2  # skip reserved

        matrix = [
            struct.unpack(">I", data[pos + i * 4 : pos + (i + 1) * 4])[0]
            for i in range(9)
        ]
        pos += 36

        width = struct.unpack(">I", data[pos : pos + 4])[0]
        height = struct.unpack(">I", data[pos + 4 : pos + 8])[0]

        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            track_id,
            duration,
            width,
            height,
            creation_time,
            modification_time,
            layer,
            alternate_group,
            volume,
            matrix,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "layer": self.layer,
            "alternate_group": self.alternate_group,
            "start": self.offset,
            "creation_time": self.creation_time,
            "modification_time": self.modification_time,
            "track_id": self.track_id,
            "duration": self.duration,
            "volume": self.volume,
            "matrix": self.matrix,
            "width": self.width,
            "height": self.height,
        }
