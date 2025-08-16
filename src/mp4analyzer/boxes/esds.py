from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import struct

from .base import MP4Box
from ..utils import bytes_to_hex


@dataclass
class DecoderSpecificInfo:
    tag: int
    size: int
    data: bytes

    def to_dict(self) -> Dict[str, object]:
        return {"tag": self.tag, "size": self.size, "data": bytes_to_hex(self.data)}


@dataclass
class SLConfigDescriptor:
    tag: int
    size: int
    data: bytes

    def to_dict(self) -> Dict[str, object]:
        return {"tag": self.tag, "size": self.size, "data": bytes_to_hex(self.data)}


@dataclass
class DecoderConfigDescriptor:
    tag: int
    size: int
    oti: int = 0
    streamType: int = 0
    upStream: bool = False
    bufferSize: int = 0
    maxBitrate: int = 0
    avgBitrate: int = 0
    decSpecificInfo: DecoderSpecificInfo | None = None

    def to_dict(self) -> Dict[str, object]:
        d = {
            "tag": self.tag,
            "size": self.size,
            "oti": self.oti,
            "streamType": self.streamType,
            "upStream": self.upStream,
            "bufferSize": self.bufferSize,
            "maxBitrate": self.maxBitrate,
            "avgBitrate": self.avgBitrate,
        }
        if self.decSpecificInfo:
            d["decSpecificInfo"] = self.decSpecificInfo.to_dict()
        return d


@dataclass
class ESDescriptor:
    tag: int
    size: int
    ES_ID: int = 0
    flags: int = 0
    dependsOn_ES_ID: int = 0
    URL: str = ""
    OCR_ES_ID: int = 0
    decoderConfig: DecoderConfigDescriptor | None = None
    slConfig: SLConfigDescriptor | None = None

    def to_dict(self) -> Dict[str, object]:
        d = {
            "tag": self.tag,
            "size": self.size,
            "ES_ID": self.ES_ID,
            "flags": self.flags,
            "dependsOn_ES_ID": self.dependsOn_ES_ID,
            "URL": self.URL,
            "OCR_ES_ID": self.OCR_ES_ID,
        }
        if self.decoderConfig:
            d["decoderConfig"] = self.decoderConfig.to_dict()
        if self.slConfig:
            d["slConfig"] = self.slConfig.to_dict()
        return d


def _parse_descriptor(data: bytes, pos: int) -> tuple[int, int, bytes, int]:
    tag = data[pos]
    pos += 1
    size = 0
    while True:
        b = data[pos]
        pos += 1
        size = (size << 7) | (b & 0x7F)
        if b & 0x80 == 0:
            break
    payload = data[pos : pos + size]
    return tag, size, payload, pos + size


def _parse_decoder_config(data: bytes) -> DecoderConfigDescriptor:
    pos = 0
    oti = data[pos]
    pos += 1
    if len(data) > pos:
        streamType = data[pos] >> 2
        upStream = bool((data[pos] >> 1) & 0x01)
    else:
        streamType = 0
        upStream = False
    pos += 1
    bufferSize = (
        struct.unpack(">I", b"\x00" + data[pos : pos + 3])[0]
        if len(data) >= pos + 3
        else 0
    )
    pos += 3
    maxBitrate = (
        struct.unpack(">I", data[pos : pos + 4])[0] if len(data) >= pos + 4 else 0
    )
    pos += 4
    avgBitrate = (
        struct.unpack(">I", data[pos : pos + 4])[0] if len(data) >= pos + 4 else 0
    )
    pos += 4
    decSpecificInfo = None
    while pos < len(data):
        tag, size, payload, new_pos = _parse_descriptor(data, pos)
        if tag == 5:
            decSpecificInfo = DecoderSpecificInfo(tag, size, payload)
        pos = new_pos
    return DecoderConfigDescriptor(
        tag=4,
        size=len(data),
        oti=oti,
        streamType=streamType,
        upStream=upStream,
        bufferSize=bufferSize,
        maxBitrate=maxBitrate,
        avgBitrate=avgBitrate,
        decSpecificInfo=decSpecificInfo,
    )


def _parse_es_descriptor(data: bytes) -> ESDescriptor:
    tag, size, payload, _ = _parse_descriptor(data, 0)
    pos = 0
    ES_ID = struct.unpack(">H", payload[pos : pos + 2])[0] if len(payload) >= 2 else 0
    pos += 2
    flags = payload[pos] if len(payload) > pos else 0
    pos += 1
    dependsOn_ES_ID = 0
    URL = ""
    OCR_ES_ID = 0
    if flags & 0x80 and len(payload) >= pos + 2:
        dependsOn_ES_ID = struct.unpack(">H", payload[pos : pos + 2])[0]
        pos += 2
    if flags & 0x40 and len(payload) > pos:
        url_len = payload[pos]
        pos += 1
        URL = payload[pos : pos + url_len].decode("utf-8", "ignore")
        pos += url_len
    if flags & 0x20 and len(payload) >= pos + 2:
        OCR_ES_ID = struct.unpack(">H", payload[pos : pos + 2])[0]
        pos += 2
    decoderConfig = None
    slConfig = None
    while pos < len(payload):
        d_tag, d_size, d_payload, new_pos = _parse_descriptor(payload, pos)
        if d_tag == 4:
            decoderConfig = _parse_decoder_config(d_payload)
            decoderConfig.tag = d_tag
            decoderConfig.size = d_size
        elif d_tag == 6:
            slConfig = SLConfigDescriptor(d_tag, d_size, d_payload)
        pos = new_pos
    return ESDescriptor(
        tag=tag,
        size=size,
        ES_ID=ES_ID,
        flags=flags,
        dependsOn_ES_ID=dependsOn_ES_ID,
        URL=URL,
        OCR_ES_ID=OCR_ES_ID,
        decoderConfig=decoderConfig,
        slConfig=slConfig,
    )


@dataclass
class ElementaryStreamDescriptorBox(MP4Box):
    """Elementary Stream Descriptor Box (``esds``)."""

    version: int = 0
    flags: int = 0
    es_descriptor: ESDescriptor | None = None
    descriptor_data: bytes = b""

    @classmethod
    def from_parsed(
        cls,
        box_type: str,
        size: int,
        offset: int,
        data: bytes,
        children: List[MP4Box] | None = None,
    ) -> "ElementaryStreamDescriptorBox":
        version = data[0] if len(data) > 0 else 0
        flags = int.from_bytes(data[1:4], "big") if len(data) >= 4 else 0
        descriptor_data = data[4:]
        es_desc = _parse_es_descriptor(descriptor_data) if descriptor_data else None
        return cls(
            box_type,
            size,
            offset,
            children or [],
            None,
            version,
            flags,
            es_desc,
            descriptor_data,
        )

    def properties(self) -> Dict[str, object]:
        props = super().properties()
        props.update(
            {
                "flags": self.flags,
                "version": self.version,
                "data": bytes_to_hex(self.descriptor_data),
            }
        )
        if self.es_descriptor:
            props["descriptor"] = self.es_descriptor.to_dict()
        return props
