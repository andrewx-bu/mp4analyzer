from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class TrackReferenceBox(MP4Box):
    """Track Reference Box (``tref``)."""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TrackReferenceBox":
        return cls(box_type, size, offset, children or [], data)

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props["data"] = bytes_to_hex(self.data)
        return props


@dataclass
class TrackReferenceTypeBox(MP4Box):
    """Generic Track Reference Type Box (e.g. ``chap``)."""

    track_ids: List[int] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TrackReferenceTypeBox":
        track_ids = []
        for i in range(0, len(data), 4):
            if i + 4 <= len(data):
                track_ids.append(int.from_bytes(data[i : i + 4], "big"))
        return cls(box_type, size, offset, children or [], data, track_ids)

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props["track_ids"] = self.track_ids
        return props
