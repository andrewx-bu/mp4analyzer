from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .base import MP4Box


@dataclass
class MovieFragmentBox(MP4Box):
    """Movie Fragment Box (``moof``)."""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "MovieFragmentBox":
        return cls(box_type, size, offset, children or [], None)
