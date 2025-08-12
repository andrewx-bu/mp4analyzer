from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class HandlerBox(MP4Box):
    """Handler Reference Box (``hdlr``)."""

    version: int = 0
    flags: int = 0
    handler: str = ""
    name: str = ""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "HandlerBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        handler = data[8:12].decode("ascii", errors="ignore")
        name_bytes = data[24:]
        name = name_bytes.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            handler,
            name,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "handler": self.handler,
            "name": self.name,
        }
