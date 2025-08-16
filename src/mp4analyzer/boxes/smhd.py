from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class SoundMediaHeaderBox(MP4Box):
    """Sound Media Header Box (``smhd``)."""

    version: int = 0
    flags: int = 0
    balance: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SoundMediaHeaderBox":
        version = data[0] if data else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        balance = struct.unpack(">h", data[4:6])[0] if len(data) >= 6 else 0
        return cls(
            box_type, size, offset, children or [], None, version, flags, balance
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "flags": self.flags,
                "version": self.version,
                "balance": self.balance,
            }
        )
        return props
