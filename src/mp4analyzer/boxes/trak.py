from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import struct

from .base import MP4Box
from .stts import TimeToSampleBox
from .stsz import SampleSizeBox


def _find_descendant(boxes: List[MP4Box], path: List[str]) -> MP4Box | None:
    if not path:
        return None
    head, *tail = path
    for box in boxes:
        if box.type == head:
            if not tail:
                return box
            return _find_descendant(box.children, tail)
    return None


def _find_descendants(boxes: List[MP4Box], box_type: str) -> List[MP4Box]:
    result: List[MP4Box] = []
    for box in boxes:
        if box.type == box_type:
            result.append(box)
        result.extend(_find_descendants(box.children, box_type))
    return result


@dataclass
class TrackBox(MP4Box):
    """Track Box (``trak``) with aggregated sample information."""

    samples_duration: int = 0
    samples_size: int = 0
    sample_groups_info: List[Dict[str, int | str]] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "TrackBox":
        children = children or []

        # Calculate total sample duration from stts box
        samples_duration = 0
        stts = _find_descendant(children, ["mdia", "minf", "stbl", "stts"])
        if isinstance(stts, TimeToSampleBox):
            samples_duration = sum(
                c * d for c, d in zip(stts.sample_counts, stts.sample_deltas)
            )
        elif stts and stts.data:
            d = stts.data
            if len(d) >= 8:
                entry_count = struct.unpack(">I", d[4:8])[0]
                pos = 8
                for _ in range(entry_count):
                    if pos + 8 > len(d):
                        break
                    count = struct.unpack(">I", d[pos : pos + 4])[0]
                    delta = struct.unpack(">I", d[pos + 4 : pos + 8])[0]
                    samples_duration += count * delta
                    pos += 8

        # Calculate total sample size from stsz box
        samples_size = 0
        stsz = _find_descendant(children, ["mdia", "minf", "stbl", "stsz"])
        if isinstance(stsz, SampleSizeBox):
            if stsz.sample_size != 0:
                samples_size = stsz.sample_size * stsz.sample_count
            else:
                samples_size = sum(stsz.sample_sizes or [])
        elif stsz and stsz.data:
            d = stsz.data
            if len(d) >= 12:
                sample_size = struct.unpack(">I", d[4:8])[0]
                sample_count = struct.unpack(">I", d[8:12])[0]
                if sample_size != 0:
                    samples_size = sample_size * sample_count
                else:
                    pos = 12
                    for _ in range(sample_count):
                        if pos + 4 > len(d):
                            break
                        samples_size += struct.unpack(">I", d[pos : pos + 4])[0]
                        pos += 4

        # Gather sample group information from sgpd boxes
        sample_groups_info: List[Dict[str, int | str]] = []
        for sgpd in _find_descendants(children, "sgpd"):
            if not sgpd.data or len(sgpd.data) < 12:
                continue
            d = sgpd.data
            grouping_type = d[4:8].decode("ascii", errors="ignore")
            entry_count = struct.unpack(">I", d[8:12])[0]
            sample_groups_info.append(
                {"grouping_type": grouping_type, "entry_count": entry_count}
            )

        return cls(
            box_type,
            size,
            offset,
            children,
            None,
            samples_duration,
            samples_size,
            sample_groups_info,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "samples_duration": self.samples_duration,
                "samples_size": self.samples_size,
                "sample_groups_info": self.sample_groups_info,
            }
        )
        return props
