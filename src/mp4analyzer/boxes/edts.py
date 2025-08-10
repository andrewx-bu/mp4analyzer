from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class EditBox(MP4Box):
    """Edit Box (``edts``)."""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "EditBox":
        return cls(box_type, size, offset, children or [], data)

    def properties(self) -> Dict[str, object]:
        return super().properties()
