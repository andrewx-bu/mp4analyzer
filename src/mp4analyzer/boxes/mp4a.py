from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List
from io import BytesIO

from .base import MP4Box


@dataclass
class MP4AudioSampleEntry(MP4Box):
    """MP4 Audio Sample Entry (``mp4a``)."""

    data_reference_index: int = 0
    version: int = 0
    channel_count: int = 0
    samplesize: int = 0
    samplerate: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "MP4AudioSampleEntry":
        data_reference_index = (
            struct.unpack(">H", data[6:8])[0] if len(data) >= 8 else 0
        )
        version = struct.unpack(">H", data[8:10])[0] if len(data) >= 10 else 0
        channel_count = struct.unpack(">H", data[16:18])[0] if len(data) >= 18 else 0
        samplesize = struct.unpack(">H", data[18:20])[0] if len(data) >= 20 else 0
        samplerate = struct.unpack(">I", data[24:28])[0] >> 16 if len(data) >= 28 else 0

        remaining = data[28:]
        child_offset_base = offset + 8 + 28
        stream = BytesIO(remaining)
        parsed_children: List[MP4Box] = []
        pos = 0
        while pos + 8 <= len(remaining):
            header = stream.read(8)
            if len(header) < 8:
                break
            child_size, child_type = struct.unpack(">I4s", header)
            if child_size < 8:
                break
            child_type_str = child_type.decode("ascii")
            payload = stream.read(child_size - 8)
            parsed_children.append(
                MP4Box(child_type_str, child_size, child_offset_base + pos, [], payload)
            )
            pos += child_size
            stream.seek(pos)

        return cls(
            box_type,
            size,
            offset,
            parsed_children,
            None,
            data_reference_index,
            version,
            channel_count,
            samplesize,
            samplerate,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "data_reference_index": self.data_reference_index,
                "version": self.version,
                "channel_count": self.channel_count,
                "samplesize": self.samplesize,
                "samplerate": self.samplerate,
            }
        )
        return props
