from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
import struct
from .base import MP4Box


@dataclass
class FileTypeBox(MP4Box):
    """The mandatory File Type Box (``ftyp``)."""

    major_brand: str = ""
    minor_version: int = 0
    compatible_brands: List[str] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "FileTypeBox":
        major_brand = data[0:4].decode("ascii")
        minor_version = struct.unpack(">I", data[4:8])[0]
        compat = [
            data[i : i + 4].decode("ascii")
            for i in range(8, len(data), 4)
            if len(data[i : i + 4]) == 4
        ]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            major_brand,
            minor_version,
            compat,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "major_brand": self.major_brand,
                "minor_version": self.minor_version,
                "compatible_brands": self.compatible_brands,
            }
        )
        return props
