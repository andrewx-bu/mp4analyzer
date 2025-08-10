from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
import struct
from .base import MP4Box


@dataclass
class MovieHeaderBox(MP4Box):
    """Movie Header Box (``mvhd``)."""

    version: int = 0
    flags: int = 0
    timescale: int = 0
    duration: int = 0
    creation_time: int = 0
    modification_time: int = 0
    rate: int = 0
    volume: float = 0.0
    matrix: List[int] = field(default_factory=list)
    next_track_id: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "MovieHeaderBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        pos = 4
        if version == 1:
            creation_time = struct.unpack(">Q", data[pos : pos + 8])[0]
            modification_time = struct.unpack(">Q", data[pos + 8 : pos + 16])[0]
            timescale = struct.unpack(">I", data[pos + 16 : pos + 20])[0]
            duration = struct.unpack(">Q", data[pos + 20 : pos + 28])[0]
            pos += 28
        else:
            creation_time = struct.unpack(">I", data[pos : pos + 4])[0]
            modification_time = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
            timescale = struct.unpack(">I", data[pos + 8 : pos + 12])[0]
            duration = struct.unpack(">I", data[pos + 12 : pos + 16])[0]
            pos += 16
        rate = struct.unpack(">I", data[pos : pos + 4])[0]
        volume = struct.unpack(">H", data[pos + 4 : pos + 6])[0] / 256
        pos += 6
        pos += 10  # reserved
        matrix = [
            struct.unpack(">I", data[pos + i * 4 : pos + (i + 1) * 4])[0]
            for i in range(9)
        ]
        pos += 36
        pos += 24  # pre-defined
        next_track_id = struct.unpack(">I", data[pos : pos + 4])[0]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            timescale,
            duration,
            creation_time,
            modification_time,
            rate,
            volume,
            matrix,
            next_track_id,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "creation_time": self.creation_time,
            "modification_time": self.modification_time,
            "timescale": self.timescale,
            "duration": self.duration,
            "rate": self.rate,
            "volume": self.volume,
            "matrix": self.matrix,
            "next_track_id": self.next_track_id,
        }
