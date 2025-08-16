from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class SampleToGroupBox(MP4Box):
    """Sample To Group Box (``sbgp``)."""

    version: int = 0
    flags: int = 0
    grouping_type: str = ""
    grouping_type_parameter: int = 0
    entries: List[Dict[str, int]] | None = None

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "SampleToGroupBox":
        version = data[0] if len(data) > 0 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        grouping_type = (
            data[4:8].decode("ascii", errors="ignore") if len(data) >= 8 else ""
        )
        pos = 8
        grouping_type_parameter = 0
        if version == 1 and len(data) >= pos + 4:
            grouping_type_parameter = struct.unpack(">I", data[pos : pos + 4])[0]
            pos += 4
        entry_count = (
            struct.unpack(">I", data[pos : pos + 4])[0] if len(data) >= pos + 4 else 0
        )
        pos += 4
        entries: List[Dict[str, int]] = []
        for _ in range(entry_count):
            if pos + 8 > len(data):
                break
            sample_count = struct.unpack(">I", data[pos : pos + 4])[0]
            group_description_index = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
            entries.append(
                {
                    "sample_count": sample_count,
                    "group_description_index": group_description_index,
                }
            )
            pos += 8
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            grouping_type,
            grouping_type_parameter,
            entries,
        )

    def properties(self) -> Dict[str, object]:
        return {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "grouping_type": self.grouping_type,
            "grouping_type_parameter": self.grouping_type_parameter,
            "entries": self.entries,
        }
