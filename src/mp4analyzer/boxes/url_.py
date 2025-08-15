from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class DataEntryUrlBox(MP4Box):
    """Data Entry URL Box (``url ``)."""

    version: int = 0
    flags: int = 0
    location: str | None = None

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "DataEntryUrlBox":
        version = data[0] if data else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        location = None
        if len(data) > 4:
            location_bytes = data[4:]
            location = location_bytes.split(b"\x00", 1)[0].decode(
                "utf-8", errors="ignore"
            )
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            location,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "flags": self.flags,
                "version": self.version,
            }
        )
        if self.location:
            props["location"] = self.location
        return props
