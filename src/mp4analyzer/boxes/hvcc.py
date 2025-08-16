from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .base import MP4Box


@dataclass
class HEVCConfigurationBox(MP4Box):
    """HEVC Configuration Box (``hvcC``)."""

    configurationVersion: int = 0
    general_profile_space: int = 0
    general_tier_flag: int = 0
    general_profile_idc: int = 0
    general_profile_compatibility: int = 0
    general_constraint_indicator: bytes = b"\x00" * 6
    general_level_idc: int = 0
    min_spatial_segmentation_idc: int = 0
    parallelismType: int = 0
    chroma_format_idc: int = 0
    bit_depth_luma_minus8: int = 0
    bit_depth_chroma_minus8: int = 0
    avgFrameRate: int = 0
    constantFrameRate: int = 0
    numTemporalLayers: int = 0
    temporalIdNested: int = 0
    lengthSizeMinusOne: int = 0
    nalu_arrays: List[List[bytes]] = field(default_factory=list)

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "HEVCConfigurationBox":
        pos = 0
        configurationVersion = data[pos] if len(data) > pos else 0
        pos += 1
        profile_byte = data[pos] if len(data) > pos else 0
        pos += 1
        general_profile_space = (profile_byte >> 6) & 0x3
        general_tier_flag = (profile_byte >> 5) & 0x1
        general_profile_idc = profile_byte & 0x1F
        general_profile_compatibility = (
            int.from_bytes(data[pos : pos + 4], "big") if len(data) >= pos + 4 else 0
        )
        pos += 4
        general_constraint_indicator = (
            data[pos : pos + 6] if len(data) >= pos + 6 else b"\x00" * 6
        )
        pos += 6
        general_level_idc = data[pos] if len(data) > pos else 0
        pos += 1
        min_spatial_segmentation_idc = (
            int.from_bytes(data[pos : pos + 2], "big") & 0x0FFF
            if len(data) >= pos + 2
            else 0
        )
        pos += 2
        parallelismType = data[pos] & 0x3 if len(data) > pos else 0
        pos += 1
        chroma_format_idc = data[pos] & 0x3 if len(data) > pos else 0
        pos += 1
        bit_depth_luma_minus8 = data[pos] & 0x7 if len(data) > pos else 0
        pos += 1
        bit_depth_chroma_minus8 = data[pos] & 0x7 if len(data) > pos else 0
        pos += 1
        avgFrameRate = (
            int.from_bytes(data[pos : pos + 2], "big") if len(data) >= pos + 2 else 0
        )
        pos += 2
        byte = data[pos] if len(data) > pos else 0
        pos += 1
        constantFrameRate = (byte >> 6) & 0x3
        numTemporalLayers = (byte >> 3) & 0x7
        temporalIdNested = (byte >> 2) & 0x1
        lengthSizeMinusOne = byte & 0x3
        numOfArrays = data[pos] if len(data) > pos else 0
        pos += 1
        nalu_arrays: List[List[bytes]] = []
        for _ in range(numOfArrays):
            if pos >= len(data):
                break
            pos += 1  # skip array_completeness/reserved/nal_unit_type
            num_nalus = (
                int.from_bytes(data[pos : pos + 2], "big")
                if len(data) >= pos + 2
                else 0
            )
            pos += 2
            nalus: List[bytes] = []
            for _ in range(num_nalus):
                if pos + 2 > len(data):
                    break
                nal_len = int.from_bytes(data[pos : pos + 2], "big")
                pos += 2
                nal = data[pos : pos + nal_len]
                pos += nal_len
                nalus.append(nal)
            nalu_arrays.append(nalus)
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            configurationVersion,
            general_profile_space,
            general_tier_flag,
            general_profile_idc,
            general_profile_compatibility,
            general_constraint_indicator,
            general_level_idc,
            min_spatial_segmentation_idc,
            parallelismType,
            chroma_format_idc,
            bit_depth_luma_minus8,
            bit_depth_chroma_minus8,
            avgFrameRate,
            constantFrameRate,
            numTemporalLayers,
            temporalIdNested,
            lengthSizeMinusOne,
            nalu_arrays,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "configurationVersion": self.configurationVersion,
                "general_profile_space": self.general_profile_space,
                "general_tier_flag": self.general_tier_flag,
                "general_profile_idc": self.general_profile_idc,
                "general_profile_compatibility": self.general_profile_compatibility,
                "general_constraint_indicator": list(self.general_constraint_indicator),
                "general_level_idc": self.general_level_idc,
                "min_spatial_segmentation_idc": self.min_spatial_segmentation_idc,
                "parallelismType": self.parallelismType,
                "chroma_format_idc": self.chroma_format_idc,
                "bit_depth_luma_minus8": self.bit_depth_luma_minus8,
                "bit_depth_chroma_minus8": self.bit_depth_chroma_minus8,
                "avgFrameRate": self.avgFrameRate,
                "constantFrameRate": self.constantFrameRate,
                "numTemporalLayers": self.numTemporalLayers,
                "temporalIdNested": self.temporalIdNested,
                "lengthSizeMinusOne": self.lengthSizeMinusOne,
                "nalu_arrays": [
                    [{"data": {str(i): b for i, b in enumerate(nal)}} for nal in arr]
                    for arr in self.nalu_arrays
                ],
            }
        )
        return props
