from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class MP4Box:
    """Represents a generic MP4 box/atom."""

    type: str
    size: int
    offset: int
    children: List["MP4Box"] = field(default_factory=list)
    # Raw payload data for boxes that are not fully parsed yet. This
    # allows other parts of the application to extract information
    # until dedicated box classes are implemented.
    data: bytes | None = None

    def properties(self) -> Dict[str, object]:
        """Return a dictionary of properties for UI display."""
        return {
            "size": self.size,
            "box_name": self.__class__.__name__,
            "start": self.offset,
        }
