from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import struct
from io import BytesIO

from .base import MP4Box
from .avcc import AVCConfigurationBox
from .colr import ColourInformationBox
from .pasp import PixelAspectRatioBox


@dataclass
class AVCSampleEntry(MP4Box):
    """AVC Sample Entry (``avc1``)."""

    data_reference_index: int = 0
    width: int = 0
    height: int = 0
    horizresolution: int = 0
    vertresolution: int = 0
    frame_count: int = 0
    compressorname: str = ""
    depth: int = 0

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "AVCSampleEntry":
        # Parse the fixed header fields of the visual sample entry
        data_reference_index = (
            struct.unpack(">H", data[6:8])[0] if len(data) >= 8 else 0
        )
        width = struct.unpack(">H", data[24:26])[0] if len(data) >= 26 else 0
        height = struct.unpack(">H", data[26:28])[0] if len(data) >= 28 else 0
        horizresolution = struct.unpack(">I", data[28:32])[0] if len(data) >= 32 else 0
        vertresolution = struct.unpack(">I", data[32:36])[0] if len(data) >= 36 else 0
        frame_count = struct.unpack(">H", data[40:42])[0] if len(data) >= 42 else 0
        name_len = data[42] if len(data) >= 43 else 0
        compressorname = (
            data[43 : 43 + name_len].decode("utf-8", "ignore")
            if len(data) >= 43 + name_len
            else ""
        )
        depth = struct.unpack(">H", data[74:76])[0] if len(data) >= 76 else 0

        # Parse child boxes from the remaining payload after the 78-byte header
        remaining = data[78:]
        child_offset_base = offset + 8 + 78
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
            if child_type_str == "avcC":
                child = AVCConfigurationBox.from_parsed(
                    child_type_str, child_size, child_offset_base + pos, payload, []
                )
            elif child_type_str == "colr":
                child = ColourInformationBox.from_parsed(
                    child_type_str, child_size, child_offset_base + pos, payload, []
                )
            elif child_type_str == "pasp":
                child = PixelAspectRatioBox.from_parsed(
                    child_type_str, child_size, child_offset_base + pos, payload, []
                )
            else:
                child = MP4Box(
                    child_type_str, child_size, child_offset_base + pos, [], payload
                )
            parsed_children.append(child)
            pos += child_size
            stream.seek(pos)

        return cls(
            box_type,
            size,
            offset,
            parsed_children,
            None,
            data_reference_index,
            width,
            height,
            horizresolution,
            vertresolution,
            frame_count,
            compressorname,
            depth,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "data_reference_index": self.data_reference_index,
                "width": self.width,
                "height": self.height,
                "horizresolution": self.horizresolution,
                "vertresolution": self.vertresolution,
                "frame_count": self.frame_count,
                "compressorname": self.compressorname,
                "depth": self.depth,
            }
        )
        return props
