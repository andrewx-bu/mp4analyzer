from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class SampleGroupDescriptionBox(MP4Box):
    """Sample Group Description Box (``sgpd``)."""

    version: int = 0
    flags: int = 0
    grouping_type: str = ""
    default_length: int = 0
    entry_count: int = 0
    used: bool = False

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SampleGroupDescriptionBox":
        version = data[0] if len(data) > 0 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        grouping_type = (
            data[4:8].decode("ascii", errors="ignore") if len(data) >= 8 else ""
        )
        pos = 8
        default_length = 0
        if version in (1, 2) and len(data) >= pos + 4:
            default_length = struct.unpack(">I", data[pos : pos + 4])[0]
            pos += 4
        entry_count = (
            struct.unpack(">I", data[pos : pos + 4])[0] if len(data) >= pos + 4 else 0
        )
        used = entry_count > 0 or default_length > 0
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            grouping_type,
            default_length,
            entry_count,
            used,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "grouping_type": self.grouping_type,
            "default_length": self.default_length,
            "used": self.used,
        }
