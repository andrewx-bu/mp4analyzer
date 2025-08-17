from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class DAC4Box(MP4Box):
    """AC-4 Specific Box (``dac4``)."""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "DAC4Box":
        return cls(box_type, size, offset, children or [], data)

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "has_unparsed_data": bool(self.data),
                "data": bytes_to_hex(self.data),
            }
        )
        return props
