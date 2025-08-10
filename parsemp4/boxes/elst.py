from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
import struct

from .base import MP4Box


@dataclass
class EditListBox(MP4Box):
    """Edit List Box (``elst``)."""

    version: int = 0
    flags: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List["MP4Box"] | None = None,
    ) -> "EditListBox":
        version = data[0]
        flags = int.from_bytes(data[1:4], "big")
        # The remainder of the payload contains ``entry_count`` followed by
        # ``entry_count`` edit list entries. For now we only extract the
        # version and flags as higher-level properties.
        # Parsing ``entry_count`` here ensures the payload is minimally
        # validated even though the individual entries are not interpreted.
        _ = struct.unpack(">I", data[4:8])[0]
        return cls(box_type, size, offset, children or [], None, version, flags)

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update({"flags": self.flags, "version": self.version})
        return props
