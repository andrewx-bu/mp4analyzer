from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class MetaBox(MP4Box):
    """Meta Box (``meta``)."""

    version: int = 0
    flags: int = 0
    is_qt: bool = False

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "MetaBox":
        version = data[0] if len(data) >= 1 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        payload = data[4:] if len(data) > 4 else b""
        return cls(
            box_type, size, offset, children or [], payload, version, flags, False
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "flags": self.flags,
                "version": self.version,
                "isQT": self.is_qt,
                "data": bytes_to_hex(self.data),
            }
        )
        return props
