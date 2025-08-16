from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class BitRateBox(MP4Box):
    """Bit Rate Box (``btrt``)."""

    bufferSizeDB: int = 0
    maxBitrate: int = 0
    avgBitrate: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "BitRateBox":
        buffer_size_db = int.from_bytes(data[0:4], "big") if len(data) >= 4 else 0
        max_bitrate = int.from_bytes(data[4:8], "big") if len(data) >= 8 else 0
        avg_bitrate = int.from_bytes(data[8:12], "big") if len(data) >= 12 else 0
        return cls(
            box_type,
            size,
            offset,
            children or [],
            data,
            buffer_size_db,
            max_bitrate,
            avg_bitrate,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "data": bytes_to_hex(self.data),
                "bufferSizeDB": self.bufferSizeDB,
                "maxBitrate": self.maxBitrate,
                "avgBitrate": self.avgBitrate,
            }
        )
        return props
