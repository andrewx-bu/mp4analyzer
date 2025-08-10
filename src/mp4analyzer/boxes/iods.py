from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from .base import MP4Box


@dataclass
class ObjectDescriptorBox(MP4Box):
    """Object Descriptor Box (``iods``)."""

    version: int = 0
    flags: int = 0
    descriptor: bytes = b""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "ObjectDescriptorBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        descriptor = data[4:]
        return cls(
            box_type, size, offset, children or [], None, version, flags, descriptor
        )

    def properties(self) -> Dict[str, object]:
        hexstr = self.descriptor.hex()
        grouped = " ".join(hexstr[i : i + 8] for i in range(0, len(hexstr), 8))
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "data": grouped,
        }
