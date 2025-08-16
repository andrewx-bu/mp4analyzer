from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import struct

from .base import MP4Box


@dataclass
class SampleDescriptionBox(MP4Box):
    """Sample Description Box (``stsd``)."""

    version: int = 0
    flags: int = 0
    entry_count: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SampleDescriptionBox":
        version = data[0] if data else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        entry_count = struct.unpack(">I", data[4:8])[0] if len(data) >= 8 else 0
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            entry_count,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "flags": self.flags,
                "version": self.version,
                "entry_count": self.entry_count,
            }
        )
        return props
