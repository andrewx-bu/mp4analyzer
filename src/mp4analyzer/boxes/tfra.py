from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import struct

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class TrackFragmentRandomAccessBox(MP4Box):
    """Track Fragment Random Access Box (``tfra``)."""

    version: int = 0
    flags: int = 0
    track_ID: int = 0
    length_size_of_traf_num: int = 0
    length_size_of_trun_num: int = 0
    length_size_of_sample_num: int = 0
    entries: List[Dict[str, int]] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TrackFragmentRandomAccessBox":
        version = data[0] if len(data) > 0 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        pos = 4
        track_ID = (
            struct.unpack(">I", data[pos : pos + 4])[0] if len(data) >= pos + 4 else 0
        )
        pos += 4
        lengths = (
            struct.unpack(">I", data[pos : pos + 4])[0] if len(data) >= pos + 4 else 0
        )
        pos += 4
        length_size_of_traf_num = (lengths >> 4) & 0x3
        length_size_of_trun_num = (lengths >> 2) & 0x3
        length_size_of_sample_num = lengths & 0x3
        entry_count = (
            struct.unpack(">I", data[pos : pos + 4])[0] if len(data) >= pos + 4 else 0
        )
        pos += 4
        entries: List[Dict[str, int]] = []
        for _ in range(entry_count):
            if version == 1:
                if len(data) < pos + 16:
                    break
                time = struct.unpack(">Q", data[pos : pos + 8])[0]
                pos += 8
                moof_offset = struct.unpack(">Q", data[pos : pos + 8])[0]
                pos += 8
            else:
                if len(data) < pos + 8:
                    break
                time = struct.unpack(">I", data[pos : pos + 4])[0]
                pos += 4
                moof_offset = struct.unpack(">I", data[pos : pos + 4])[0]
                pos += 4
            traf_len = length_size_of_traf_num + 1
            trun_len = length_size_of_trun_num + 1
            sample_len = length_size_of_sample_num + 1
            if len(data) < pos + traf_len + trun_len + sample_len:
                break
            traf_number = int.from_bytes(data[pos : pos + traf_len], "big")
            pos += traf_len
            trun_number = int.from_bytes(data[pos : pos + trun_len], "big")
            pos += trun_len
            sample_number = int.from_bytes(data[pos : pos + sample_len], "big")
            pos += sample_len
            entries.append(
                {
                    "time": time,
                    "moof_offset": moof_offset,
                    "traf_number": traf_number,
                    "trun_number": trun_number,
                    "sample_number": sample_number,
                }
            )
        return cls(
            box_type,
            size,
            offset,
            children or [],
            data,
            version,
            flags,
            track_ID,
            length_size_of_traf_num,
            length_size_of_trun_num,
            length_size_of_sample_num,
            entries,
        )

    def properties(self) -> Dict[str, object]:
        props = {
            "size": self.size,
            "flags": self.flags,
            "version": self.version,
            "box_name": self.__class__.__name__,
            "start": self.offset,
            "data": bytes_to_hex(self.data[4:] if self.data else b""),
            "track_ID": self.track_ID,
            "length_size_of_traf_num": self.length_size_of_traf_num,
            "length_size_of_trun_num": self.length_size_of_trun_num,
            "length_size_of_sample_num": self.length_size_of_sample_num,
        }
        if self.entries:
            props.update(self.entries[0])
        return props
