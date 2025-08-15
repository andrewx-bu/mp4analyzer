from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List, Dict

from .base import MP4Box


@dataclass
class VideoMediaHeaderBox(MP4Box):
    """Video Media Header Box (``vmhd``)."""

    version: int = 0
    flags: int = 0
    graphicsmode: int = 0
    opcolor: List[int] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "VideoMediaHeaderBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        graphicsmode = struct.unpack(">H", data[4:6])[0]
        opcolor = list(struct.unpack(">HHH", data[6:12]))
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            graphicsmode,
            opcolor,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "graphicsmode": self.graphicsmode,
            "opcolor": self.opcolor,
        }
