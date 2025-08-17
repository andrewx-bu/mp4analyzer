from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class FieldHandlingBox(MP4Box):
    """Field Handling Box (``fiel``).

    Stores how interlaced video fields are ordered.
    """

    fieldCount: int = 0
    fieldOrdering: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "FieldHandlingBox":
        field_count = data[0] if len(data) >= 1 else 0
        field_ordering = data[1] if len(data) >= 2 else 0
        return cls(
            box_type, size, offset, children or [], data, field_count, field_ordering
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "data": bytes_to_hex(self.data),
                "fieldCount": self.fieldCount,
                "fieldOrdering": self.fieldOrdering,
            }
        )
        return props
