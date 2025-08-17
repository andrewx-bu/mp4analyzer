from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .base import MP4Box
from .data import DataBox
from ..utils import bytes_to_hex


@dataclass
class IlstBox(MP4Box):
    """Item List Box (``ilst``) containing iTunes metadata entries."""

    items: Dict[int, DataBox] = field(default_factory=dict)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "IlstBox":
        items: Dict[int, DataBox] = {}
        pos = 0
        while pos + 8 <= len(data):
            item_size = int.from_bytes(data[pos : pos + 4], "big")
            if item_size < 8 or pos + item_size > len(data):
                break
            item_type = int.from_bytes(data[pos + 4 : pos + 8], "big")
            item_payload = data[pos + 8 : pos + item_size]
            if len(item_payload) >= 8:
                db_size = int.from_bytes(item_payload[0:4], "big")
                db_type = item_payload[4:8].decode("ascii", errors="ignore")
                if db_type == "data" and db_size <= len(item_payload):
                    db_data = item_payload[8:db_size]
                    db_offset = offset + 8 + pos + 8
                    items[item_type] = DataBox.from_parsed(
                        "data", db_size, db_offset, db_data, []
                    )
            pos += item_size
        return cls(box_type, size, offset, [], data, items)

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props["data"] = bytes_to_hex(self.data)
        props["list"] = {str(k): v.properties() for k, v in self.items.items()}
        return props
