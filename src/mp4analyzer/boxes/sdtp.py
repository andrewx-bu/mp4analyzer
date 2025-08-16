from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..utils import bytes_to_hex
from .base import MP4Box


@dataclass
class SampleDependencyTypeBox(MP4Box):
    """Sample Dependency Type Box (``sdtp``)."""

    version: int = 0
    flags: int = 0
    is_leading: List[int] | None = None
    sample_depends_on: List[int] | None = None
    sample_is_depended_on: List[int] | None = None
    sample_has_redundancy: List[int] | None = None

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SampleDependencyTypeBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        entries = data[4:]
        is_leading: List[int] = []
        sample_depends_on: List[int] = []
        sample_is_depended_on: List[int] = []
        sample_has_redundancy: List[int] = []
        for b in entries:
            is_leading.append((b >> 6) & 0x03)
            sample_depends_on.append((b >> 4) & 0x03)
            sample_is_depended_on.append((b >> 2) & 0x03)
            sample_has_redundancy.append(b & 0x03)
        return cls(
            box_type,
            size,
            offset,
            children or [],
            entries,
            version,
            flags,
            is_leading,
            sample_depends_on,
            sample_is_depended_on,
            sample_has_redundancy,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "data": bytes_to_hex(self.data),
            "is_leading": self.is_leading,
            "sample_depends_on": self.sample_depends_on,
            "sample_is_depended_on": self.sample_is_depended_on,
            "sample_has_redundancy": self.sample_has_redundancy,
        }
