from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class ColourInformationBox(MP4Box):
    """Colour Information Box (``colr``)."""

    colour_type: str = ""
    colour_primaries: int = 0
    transfer_characteristics: int = 0
    matrix_coefficients: int = 0
    full_range_flag: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "ColourInformationBox":
        colour_type = data[0:4].decode("ascii") if len(data) >= 4 else ""
        colour_primaries = int.from_bytes(data[4:6], "big") if len(data) >= 6 else 0
        transfer_characteristics = (
            int.from_bytes(data[6:8], "big") if len(data) >= 8 else 0
        )
        matrix_coefficients = (
            int.from_bytes(data[8:10], "big") if len(data) >= 10 else 0
        )
        full_range_flag = (data[10] & 0x80) >> 7 if len(data) >= 11 else 0
        return cls(
            box_type,
            size,
            offset,
            children or [],
            data,
            colour_type,
            colour_primaries,
            transfer_characteristics,
            matrix_coefficients,
            full_range_flag,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "data": bytes_to_hex(self.data),
                "colour_type": self.colour_type,
                "colour_primaries": self.colour_primaries,
                "transfer_characteristics": self.transfer_characteristics,
                "matrix_coefficients": self.matrix_coefficients,
                "full_range_flag": self.full_range_flag,
            }
        )
        return props
