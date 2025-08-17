from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .mp4a import MP4AudioSampleEntry
from .dac4 import DAC4Box
from .base import MP4Box


@dataclass
class AC4SampleEntry(MP4AudioSampleEntry):
    """AC-4 Sample Entry (``ac-4``)."""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "AC4SampleEntry":
        base = MP4AudioSampleEntry.from_parsed(box_type, size, offset, data, children)
        parsed_children: List[MP4Box] = []
        for child in base.children:
            if child.type == "dac4":
                parsed_children.append(
                    DAC4Box.from_parsed(
                        child.type, child.size, child.offset, child.data or b"", []
                    )
                )
            else:
                parsed_children.append(child)
        return cls(
            base.type,
            base.size,
            base.offset,
            parsed_children,
            base.data,
            base.data_reference_index,
            base.version,
            base.channel_count,
            base.samplesize,
            base.samplerate,
        )
