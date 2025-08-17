from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .base import MP4Box


@dataclass
class AV1CodecConfigurationBox(MP4Box):
    """AV1 Codec Configuration Box (``av1C``)."""

    configurationVersion: int = 0
    seq_profile: int = 0
    seq_level_idx_0: int = 0
    seq_tier_0: int = 0
    high_bitdepth: int = 0
    twelve_bit: int = 0
    monochrome: int = 0
    chroma_subsampling_x: int = 0
    chroma_subsampling_y: int = 0
    chroma_sample_position: int = 0
    initial_presentation_delay_present: int = 0
    initial_presentation_delay_minus_one: int = 0
    configOBUs: bytes = b""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "AV1CodecConfigurationBox":
        b0 = data[0] if len(data) > 0 else 0
        b1 = data[1] if len(data) > 1 else 0
        b2 = data[2] if len(data) > 2 else 0
        b3 = data[3] if len(data) > 3 else 0

        configurationVersion = b0 & 0x7F
        seq_profile = (b1 >> 5) & 0x7
        seq_level_idx_0 = b1 & 0x1F
        seq_tier_0 = (b2 >> 7) & 0x1
        high_bitdepth = (b2 >> 6) & 0x1
        twelve_bit = (b2 >> 5) & 0x1
        monochrome = (b2 >> 4) & 0x1
        chroma_subsampling_x = (b2 >> 3) & 0x1
        chroma_subsampling_y = (b2 >> 2) & 0x1
        chroma_sample_position = b2 & 0x3
        initial_presentation_delay_present = (b3 >> 4) & 0x1
        initial_presentation_delay_minus_one = b3 & 0x0F
        configOBUs = data[4:] if len(data) > 4 else b""

        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            configurationVersion,
            seq_profile,
            seq_level_idx_0,
            seq_tier_0,
            high_bitdepth,
            twelve_bit,
            monochrome,
            chroma_subsampling_x,
            chroma_subsampling_y,
            chroma_sample_position,
            initial_presentation_delay_present,
            initial_presentation_delay_minus_one,
            configOBUs,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "configurationVersion": self.configurationVersion,
                "seq_profile": self.seq_profile,
                "seq_level_idx_0": self.seq_level_idx_0,
                "seq_tier_0": self.seq_tier_0,
                "high_bitdepth": self.high_bitdepth,
                "twelve_bit": self.twelve_bit,
                "monochrome": self.monochrome,
                "chroma_subsampling_x": self.chroma_subsampling_x,
                "chroma_subsampling_y": self.chroma_subsampling_y,
                "chroma_sample_position": self.chroma_sample_position,
                "initial_presentation_delay_present": self.initial_presentation_delay_present,
                "initial_presentation_delay_minus_one": self.initial_presentation_delay_minus_one,
                "configOBUs": list(self.configOBUs),
            }
        )
        return props
