from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import struct

from .base import MP4Box


@dataclass
class ChapterEntry:
    start_time: int
    duration: int
    title: str


@dataclass
class ChapterListBox(MP4Box):
    """Chapter List Box (``chpl``)."""

    version: int = 0
    flags: int = 0
    chapters: List[ChapterEntry] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "ChapterListBox":
        version = data[0] if data else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        entry_count = struct.unpack(">I", data[4:8])[0] if len(data) >= 8 else 0
        pos = 8
        chapters: List[ChapterEntry] = []

        # If entry_count appears to be zero but data remains, attempt to parse all entries.
        estimated = entry_count if entry_count else 0
        while pos + 8 < len(data) and (estimated == 0 or len(chapters) < estimated):
            start_time = struct.unpack(">I", data[pos : pos + 4])[0]
            duration = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
            pos += 8
            if pos >= len(data):
                break
            name_len = data[pos]
            pos += 1
            title = data[pos : pos + name_len].decode("utf-8", "ignore")
            pos += name_len
            chapters.append(ChapterEntry(start_time, duration, title))

        return cls(
            box_type, size, offset, children or [], None, version, flags, chapters
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update({"version": self.version, "flags": self.flags})
        props["chapters"] = [
            {"start_time": c.start_time, "duration": c.duration, "title": c.title}
            for c in self.chapters
        ]
        return props
