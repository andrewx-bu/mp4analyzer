from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import struct

from .base import MP4Box
from .tfhd import TrackFragmentHeaderBox
from .trun import TrackRunBox

_TRACK_SAMPLE_COUNTER: Dict[int, int] = {}


@dataclass
class TrackFragmentBox(MP4Box):
    """Track Fragment Box (``traf``) with aggregated sample info."""

    sample_number: int = 0
    first_sample_index: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TrackFragmentBox":
        children = children or []
        track_id = 0
        sample_number = 0
        for child in children:
            if isinstance(child, TrackFragmentHeaderBox):
                track_id = child.track_id
            elif isinstance(child, TrackRunBox):
                sample_number += child.sample_count
        counter = _TRACK_SAMPLE_COUNTER.get(track_id, 0)
        first_sample_index = counter + 1 if track_id else 0
        _TRACK_SAMPLE_COUNTER[track_id] = counter + sample_number
        return cls(
            box_type, size, offset, children, None, sample_number, first_sample_index
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "sample_number": self.sample_number,
                "first_sample_index": self.first_sample_index,
            }
        )
        return props

    @classmethod
    def reset_counters(cls) -> None:
        _TRACK_SAMPLE_COUNTER.clear()
