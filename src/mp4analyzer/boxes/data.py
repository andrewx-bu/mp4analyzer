from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class DataBox(MP4Box):
    """iTunes-style metadata data box (``data``)."""

    value_type: int = 0
    country: int = 0
    language: int = 0
    raw: bytes = b""
    value: str = ""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "DataBox":
        value_type = int.from_bytes(data[0:4], "big") if len(data) >= 4 else 0
        locale = int.from_bytes(data[4:8], "big") if len(data) >= 8 else 0
        country = (locale >> 16) & 0xFFFF
        language = locale & 0xFFFF
        raw = data[8:] if len(data) > 8 else b""
        value = raw.decode("utf-8", errors="ignore")
        return cls(
            box_type,
            size,
            offset,
            children or [],
            data,
            value_type,
            country,
            language,
            raw,
            value,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "hdr_size": 8,
                "data": {str(i): b for i, b in enumerate(self.data)},
                "valueType": self.value_type,
                "country": self.country,
                "language": self.language,
                "raw": {str(i): b for i, b in enumerate(self.raw)},
                "value": self.value,
            }
        )
        return props
