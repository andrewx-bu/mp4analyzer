from __future__ import annotations
from dataclasses import dataclass

from .base import MP4Box


@dataclass
class MediaDataBox(MP4Box):
    """Represents an ``mdat`` box containing media data.

    The payload is not loaded to avoid consuming large amounts of memory.
    """
