from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from .base import MP4Box


@dataclass
class DataInformationBox(MP4Box):
    """Data Information Box (``dinf``)."""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "DataInformationBox":
        return cls(box_type, size, offset, children or [], None)

    def properties(self) -> Dict[str, object]:
        return super().properties()
