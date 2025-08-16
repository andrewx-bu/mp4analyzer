from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class PixelAspectRatioBox(MP4Box):
    """Pixel Aspect Ratio Box (``pasp``)."""

    hSpacing: int = 0
    vSpacing: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "PixelAspectRatioBox":
        h_spacing = int.from_bytes(data[0:4], "big") if len(data) >= 4 else 0
        v_spacing = int.from_bytes(data[4:8], "big") if len(data) >= 8 else 0
        return cls(box_type, size, offset, children or [], data, h_spacing, v_spacing)

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "data": bytes_to_hex(self.data),
                "hSpacing": self.hSpacing,
                "vSpacing": self.vSpacing,
            }
        )
        return props
