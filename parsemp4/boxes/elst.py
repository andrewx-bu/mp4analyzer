from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import struct

from .base import MP4Box


@dataclass
class EditListEntry:
    """Represents a single ``elst`` entry."""

    segment_duration: int
    media_time: int
    media_rate_integer: int
    media_rate_fraction: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "segment_duration": self.segment_duration,
            "media_time": self.media_time,
            "media_rate_integer": self.media_rate_integer,
            "media_rate_fraction": self.media_rate_fraction,
        }


@dataclass
class EditListBox(MP4Box):
    """Edit List Box (``elst``)."""

    version: int = 0
    flags: int = 0
    entries: List[EditListEntry] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "EditListBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        entry_count = struct.unpack(">I", data[4:8])[0]
        pos = 8
        entries: List[EditListEntry] = []
        for _ in range(entry_count):
            if version == 1:
                segment_duration = struct.unpack(">Q", data[pos : pos + 8])[0]
                media_time = struct.unpack(">q", data[pos + 8 : pos + 16])[0]
                pos += 16
            else:
                segment_duration = struct.unpack(">I", data[pos : pos + 4])[0]
                media_time = struct.unpack(">i", data[pos + 4 : pos + 8])[0]
                pos += 8
            media_rate_integer = struct.unpack(">h", data[pos : pos + 2])[0]
            media_rate_fraction = struct.unpack(">h", data[pos + 2 : pos + 4])[0]
            pos += 4
            entries.append(
                EditListEntry(
                    segment_duration,
                    media_time,
                    media_rate_integer,
                    media_rate_fraction,
                )
            )
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            entries,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "flags": self.flags,
                "version": self.version,
                "entry_count": len(self.entries),
                "entries": [entry.to_dict() for entry in self.entries],
            }
        )
        return props
