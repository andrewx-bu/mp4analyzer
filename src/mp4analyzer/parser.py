from typing import BinaryIO, List, Dict, Type
import os
import struct
from .boxes import (
    MP4Box,
    FileTypeBox,
    MovieHeaderBox,
    TrackHeaderBox,
    MediaHeaderBox,
    ObjectDescriptorBox,
    MovieBox,
    TrackBox,
    FreeSpaceBox,
    MediaDataBox,
    EditBox,
    EditListBox,
    HandlerBox,
    MediaInformationBox,
    VideoMediaHeaderBox,
    DataInformationBox,
    DataReferenceBox,
    DataEntryUrlBox,
    SampleTableBox,
    SampleDescriptionBox,
    AVCSampleEntry,
    AVCConfigurationBox,
    ColourInformationBox,
    PixelAspectRatioBox,
    TimeToSampleBox,
    CompositionOffsetBox,
    SyncSampleBox,
    SampleDependencyTypeBox,
    SampleToChunkBox,
    SampleSizeBox,
    ChunkOffsetBox,
)


# Common container box types that can contain child boxes
CONTAINER_BOX_TYPES = {
    "moov",
    "trak",
    "mdia",
    "minf",
    "stbl",
    "edts",
    "dinf",
    "dref",
    "mvex",
    "moof",
    "traf",
    "mfra",
    "udta",
    "meta",
    "ilst",
    "tref",
    "stsd",
    "sinf",
    "schi",
    "strk",
    "strd",
    "senc",
}

# Mapping of box type to specialised box class
BOX_PARSERS: Dict[str, Type[MP4Box]] = {
    "ftyp": FileTypeBox,
    "mvhd": MovieHeaderBox,
    "tkhd": TrackHeaderBox,
    "mdhd": MediaHeaderBox,
    "iods": ObjectDescriptorBox,
    "moov": MovieBox,
    "trak": TrackBox,
    "free": FreeSpaceBox,
    "edts": EditBox,
    "elst": EditListBox,
    "hdlr": HandlerBox,
    "minf": MediaInformationBox,
    "vmhd": VideoMediaHeaderBox,
    "dinf": DataInformationBox,
    "dref": DataReferenceBox,
    "url ": DataEntryUrlBox,
    "stbl": SampleTableBox,
    "stsd": SampleDescriptionBox,
    "avc1": AVCSampleEntry,
    "avcC": AVCConfigurationBox,
    "colr": ColourInformationBox,
    "pasp": PixelAspectRatioBox,
    "stts": TimeToSampleBox,
    "ctts": CompositionOffsetBox,
    "stss": SyncSampleBox,
    "sdtp": SampleDependencyTypeBox,
    "stsc": SampleToChunkBox,
    "stsz": SampleSizeBox,
    "stco": ChunkOffsetBox,
}

# Box types for which raw payload data should be captured for later processing
RAW_DATA_BOX_TYPES = {"stsd", "stts", "sbgp", "sgpd"}


def _read_u64(f: BinaryIO) -> int:
    data = f.read(8)
    if len(data) != 8:
        raise EOFError("Unexpected end of file")
    return struct.unpack(">Q", data)[0]


def _parse_box(
    f: BinaryIO, file_size: int, parent_end: int | None = None
) -> MP4Box | None:
    start_offset = f.tell()
    if parent_end is not None and start_offset >= parent_end:
        return None

    header = f.read(8)
    if len(header) < 8:
        return None

    size, box_type = struct.unpack(">I4s", header)
    box_type = box_type.decode("ascii")

    header_size = 8
    if size == 1:  # 64-bit extended size
        size = _read_u64(f)
        header_size = 16
    elif size == 0:
        # box extends to end of file or parent
        size = (parent_end if parent_end is not None else file_size) - start_offset

    payload_size = size - header_size
    payload_end = start_offset + size

    if box_type == "mdat":
        f.seek(payload_size, os.SEEK_CUR)
        return MediaDataBox(box_type, size, start_offset)

    children: List[MP4Box] = []
    data: bytes | None = None

    if box_type in {"dref", "stsd"}:
        # ``dref`` and ``stsd`` are container FullBoxes with an entry count
        # preceding their child boxes
        if payload_size >= 8:
            data = f.read(8)
        else:
            data = f.read(payload_size)
        while f.tell() < payload_end:
            child = _parse_box(f, file_size, payload_end)
            if not child:
                break
            children.append(child)
    elif box_type in CONTAINER_BOX_TYPES and payload_size > 8:
        while f.tell() < payload_end:
            child = _parse_box(f, file_size, payload_end)
            if not child:
                break
            children.append(child)
    else:
        if payload_size > 0 and (
            box_type in BOX_PARSERS or box_type in RAW_DATA_BOX_TYPES
        ):
            data = f.read(payload_size)
        else:
            f.seek(payload_size, os.SEEK_CUR)

    box_cls = BOX_PARSERS.get(box_type)
    if box_cls:
        # For parsed boxes we expect data to be present
        parsed_box = box_cls.from_parsed(
            box_type, size, start_offset, data or b"", children
        )
        return parsed_box

    return MP4Box(box_type, size, start_offset, children, data)


def parse_mp4_boxes(file_path: str) -> List[MP4Box]:
    """Parse top-level MP4 boxes from a file."""
    file_size = os.path.getsize(file_path)
    boxes: List[MP4Box] = []
    with open(file_path, "rb") as f:
        while f.tell() < file_size:
            box = _parse_box(f, file_size)
            if not box:
                break
            boxes.append(box)
    return boxes
