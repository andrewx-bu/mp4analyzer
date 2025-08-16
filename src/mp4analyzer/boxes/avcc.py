from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import struct

from .base import MP4Box


@dataclass
class AVCConfigurationBox(MP4Box):
    """AVC Configuration Box (``avcC``)."""

    configurationVersion: int = 0
    AVCProfileIndication: int = 0
    profile_compatibility: int = 0
    AVCLevelIndication: int = 0
    lengthSizeMinusOne: int = 0
    sps: List[bytes] = field(default_factory=list)
    pps: List[bytes] = field(default_factory=list)
    ext: bytes = b""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "AVCConfigurationBox":
        pos = 0
        configurationVersion = data[pos] if len(data) > pos else 0
        pos += 1
        AVCProfileIndication = data[pos] if len(data) > pos else 0
        pos += 1
        profile_compatibility = data[pos] if len(data) > pos else 0
        pos += 1
        AVCLevelIndication = data[pos] if len(data) > pos else 0
        pos += 1
        lengthSizeMinusOne = data[pos] & 0x3 if len(data) > pos else 0
        pos += 1
        num_sps = data[pos] & 0x1F if len(data) > pos else 0
        pos += 1
        sps: List[bytes] = []
        for _ in range(num_sps):
            if pos + 2 > len(data):
                break
            sps_len = struct.unpack(">H", data[pos : pos + 2])[0]
            pos += 2
            sps.append(data[pos : pos + sps_len])
            pos += sps_len
        num_pps = data[pos] if len(data) > pos else 0
        pos += 1
        pps: List[bytes] = []
        for _ in range(num_pps):
            if pos + 2 > len(data):
                break
            pps_len = struct.unpack(">H", data[pos : pos + 2])[0]
            pos += 2
            pps.append(data[pos : pos + pps_len])
            pos += pps_len
        ext = data[pos:]
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            configurationVersion,
            AVCProfileIndication,
            profile_compatibility,
            AVCLevelIndication,
            lengthSizeMinusOne,
            sps,
            pps,
            ext,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "configurationVersion": self.configurationVersion,
                "AVCProfileIndication": self.AVCProfileIndication,
                "profile_compatibility": self.profile_compatibility,
                "AVCLevelIndication": self.AVCLevelIndication,
                "lengthSizeMinusOne": self.lengthSizeMinusOne,
                "nb_SPS_nalus": len(self.sps),
                "SPS": [
                    {"length": len(s), "nalu_data": "0x" + s.hex()} for s in self.sps
                ],
                "nb_PPS_nalus": len(self.pps),
                "PPS": [
                    {"length": len(p), "nalu_data": "0x" + p.hex()} for p in self.pps
                ],
                "ext": list(self.ext),
            }
        )
        return props
