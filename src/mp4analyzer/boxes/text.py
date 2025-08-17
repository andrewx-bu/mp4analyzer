from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import struct

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class TextSampleEntry(MP4Box):
    """Text Sample Entry (``text``)."""

    data_reference_index: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TextSampleEntry":
        data_reference_index = (
            struct.unpack(">H", data[6:8])[0] if len(data) >= 8 else 0
        )
        remaining = data[8:]
        return cls(
            box_type, size, offset, children or [], remaining, data_reference_index
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props["data_reference_index"] = self.data_reference_index
        if self.data:
            props["data"] = bytes_to_hex(self.data)
        return props
