from typing import BinaryIO, List, Optional, Dict, Type
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
    MovieFragmentBox,
    MovieFragmentRandomAccessBox,
    MovieFragmentHeaderBox,
    TrackFragmentBox,
    TrackFragmentHeaderBox,
    TrackFragmentBaseMediaDecodeTimeBox,
    TrackRunBox,
    TrackFragmentRandomAccessBox,
    MovieExtendsBox,
    MovieExtendsHeaderBox,
    TrackExtendsBox,
    TrackBox,
    FreeSpaceBox,
    MediaDataBox,
    EditBox,
    EditListBox,
    HandlerBox,
    MediaBox,
    MediaInformationBox,
    MetaBox,
    IlstBox,
    VideoMediaHeaderBox,
    SoundMediaHeaderBox,
    DataInformationBox,
    DataReferenceBox,
    DataEntryUrlBox,
    SampleTableBox,
    SampleDescriptionBox,
    AVCSampleEntry,
    HEVCSampleEntry,
    AV1SampleEntry,
    MP4AudioSampleEntry,
    AC4SampleEntry,
    AVCConfigurationBox,
    HEVCConfigurationBox,
    AV1CodecConfigurationBox,
    BitRateBox,
    ColourInformationBox,
    PixelAspectRatioBox,
    FieldHandlingBox,
    TimeToSampleBox,
    CompositionOffsetBox,
    SyncSampleBox,
    SampleDependencyTypeBox,
    SampleToChunkBox,
    SampleSizeBox,
    ChunkOffsetBox,
    SampleGroupDescriptionBox,
    SampleToGroupBox,
    UserDataBox,
    TrackReferenceBox,
    TrackReferenceTypeBox,
    ElementaryStreamDescriptorBox,
    ChapterListBox,
    TextSampleEntry,
    GenericMediaHeaderBox,
    DAC4Box,
    MovieFragmentRandomAccessOffsetBox,
)

# Box types that can contain children
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
    "tref",
    "stsd",
    "sinf",
    "schi",
    "strk",
    "strd",
    "senc",
}

# Mapping of type → parser class
BOX_PARSERS: Dict[str, Type[MP4Box]] = {
    "ftyp": FileTypeBox,
    "mvhd": MovieHeaderBox,
    "tkhd": TrackHeaderBox,
    "mdhd": MediaHeaderBox,
    "iods": ObjectDescriptorBox,
    "moov": MovieBox,
    "moof": MovieFragmentBox,
    "mfra": MovieFragmentRandomAccessBox,
    "mfhd": MovieFragmentHeaderBox,
    "traf": TrackFragmentBox,
    "tfhd": TrackFragmentHeaderBox,
    "tfdt": TrackFragmentBaseMediaDecodeTimeBox,
    "trun": TrackRunBox,
    "tfra": TrackFragmentRandomAccessBox,
    "mfro": MovieFragmentRandomAccessOffsetBox,
    "mvex": MovieExtendsBox,
    "mehd": MovieExtendsHeaderBox,
    "trex": TrackExtendsBox,
    "trak": TrackBox,
    "mdia": MediaBox,
    "udta": UserDataBox,
    "tref": TrackReferenceBox,
    "free": FreeSpaceBox,
    "edts": EditBox,
    "elst": EditListBox,
    "hdlr": HandlerBox,
    "minf": MediaInformationBox,
    "meta": MetaBox,
    "ilst": IlstBox,
    "vmhd": VideoMediaHeaderBox,
    "smhd": SoundMediaHeaderBox,
    "dinf": DataInformationBox,
    "dref": DataReferenceBox,
    "url ": DataEntryUrlBox,
    "stbl": SampleTableBox,
    "stsd": SampleDescriptionBox,
    "avc1": AVCSampleEntry,
    "hev1": HEVCSampleEntry,
    "av01": AV1SampleEntry,
    "mp4a": MP4AudioSampleEntry,
    "ac-4": AC4SampleEntry,
    "avcC": AVCConfigurationBox,
    "hvcC": HEVCConfigurationBox,
    "av1C": AV1CodecConfigurationBox,
    "btrt": BitRateBox,
    "colr": ColourInformationBox,
    "pasp": PixelAspectRatioBox,
    "fiel": FieldHandlingBox,
    "esds": ElementaryStreamDescriptorBox,
    "stts": TimeToSampleBox,
    "ctts": CompositionOffsetBox,
    "stss": SyncSampleBox,
    "sdtp": SampleDependencyTypeBox,
    "stsc": SampleToChunkBox,
    "stsz": SampleSizeBox,
    "stco": ChunkOffsetBox,
    "sgpd": SampleGroupDescriptionBox,
    "sbgp": SampleToGroupBox,
    "chap": TrackReferenceTypeBox,
    "chpl": ChapterListBox,
    "text": TextSampleEntry,
    "gmhd": GenericMediaHeaderBox,
    "dac4": DAC4Box,
}

# Keep raw payloads for later
RAW_DATA_BOX_TYPES = {
    "stsd",
    "stts",
    "sbgp",
    "sgpd",
}


def _read_box_header(f: BinaryIO, file_size: int):
    """Read an ISO BMFF box header at current file position."""
    start_pos = f.tell()
    if start_pos + 8 > file_size:
        return None

    header = f.read(8)
    if len(header) < 8:
        return None

    size32, type_bytes = struct.unpack(">I4s", header)
    try:
        btype = type_bytes.decode("ascii")
    except UnicodeDecodeError:
        btype = type_bytes.hex()

    header_len = 8
    box_size = size32

    if box_size == 1:
        # 64-bit largesize
        if start_pos + 16 > file_size:
            return None
        big = f.read(8)
        if len(big) < 8:
            return None
        (box_size,) = struct.unpack(">Q", big)
        header_len = 16

    if btype == "uuid":
        # 16-byte extended type GUID
        if start_pos + header_len + 16 > file_size:
            return None
        _ = f.read(16)
        header_len += 16

    if box_size == 0:
        # Extends to end of file
        box_size = file_size - start_pos

    if box_size < header_len:
        return None

    return (box_size, btype, header_len, start_pos)


def _parse_box(
    f: BinaryIO,
    file_size: int,
    parent_end: Optional[int] = None,
    stream_offset: int = 0,
) -> "MP4Box | None":
    """Parse one box from file or memory."""
    start = stream_offset + f.tell()
    if parent_end is not None and start >= parent_end:
        return None

    # Read header (support 64-bit sizes, uuid, size==0)
    hdr = _read_box_header(f, file_size if parent_end is None else parent_end)
    if hdr is None:
        return None
    size, btype, hdr_size, start_real = hdr
    payload_size = size - hdr_size
    end = start_real + size

    # Fast skip of raw media data
    if btype == "mdat":
        f.seek(end - (stream_offset + f.tell()), os.SEEK_CUR)  # jump to end of box
        return MediaDataBox(btype, size, start_real)

    children: List["MP4Box"] = []
    data: Optional[bytes] = None

    # Container-like boxes with special headers/prefixes
    if btype in {"dref", "stsd"}:
        # Read 8 bytes of version/flags + entry_count, then parse children
        data = f.read(min(8, payload_size))
        while stream_offset + f.tell() < end:
            child = _parse_box(f, file_size, end, stream_offset)
            if not child:
                break
            children.append(child)

    elif btype == "meta":
        # meta has a fullbox header (4 bytes) then sub-boxes
        payload = f.read(payload_size)
        header4 = payload[:4]
        import io as _io

        substream = _io.BytesIO(payload[4:])
        sub_offset = start_real + hdr_size + 4
        sub_end = sub_offset + len(payload) - 4
        while substream.tell() + sub_offset < sub_end:
            child = _parse_box(substream, sub_end, sub_end, sub_offset)
            if not child:
                break
            children.append(child)
        data = header4 + payload[4:]

    elif btype == "tref":
        # tref is a container of references (no extra prefix)
        payload = f.read(payload_size)
        import io as _io

        substream = _io.BytesIO(payload)
        sub_offset = start_real + hdr_size
        sub_end = sub_offset + len(payload)
        while substream.tell() + sub_offset < sub_end:
            child = _parse_box(substream, sub_end, sub_end, sub_offset)
            if not child:
                break
            children.append(child)
        data = payload

    elif btype in CONTAINER_BOX_TYPES and payload_size > 0:
        # Generic container
        while stream_offset + f.tell() < end:
            child = _parse_box(f, file_size, end, stream_offset)
            if not child:
                break
            children.append(child)

    else:
        # Leaf box (parse or skip)
        if payload_size > 0 and (btype in BOX_PARSERS or btype in RAW_DATA_BOX_TYPES):
            data = f.read(payload_size)
        else:
            # Skip unknown/unsupported payload to keep forward progress
            f.seek(payload_size, os.SEEK_CUR)

    # Build classed box if available
    box_cls = BOX_PARSERS.get(btype)
    if box_cls and hasattr(box_cls, "from_parsed"):
        return getattr(box_cls, "from_parsed")(
            btype, size, start_real, data or b"", children
        )
    return MP4Box(btype, size, start_real, children, data)


def parse_mp4_boxes_streaming(
    file_path: str, max_memory_mb: int = 50
) -> List["MP4Box"]:
    """
    Parse top-level MP4 boxes using a memory-conscious streaming approach.
    For very large 'mdat' boxes, record metadata and seek past payload.
    """
    file_size = os.path.getsize(file_path)
    boxes: List["MP4Box"] = []
    max_memory_bytes = max_memory_mb * 1024 * 1024

    TrackFragmentBox.reset_counters()

    with open(file_path, "rb") as f:
        while f.tell() < file_size:
            hdr = _read_box_header(f, file_size)
            if hdr is None:
                break
            box_size, btype, header_len, start_pos = hdr

            # Large mdat: record and skip
            if btype == "mdat" and box_size > max_memory_bytes:
                try:
                    boxes.append(MediaDataBox(btype, box_size, start_pos))
                except NameError:
                    pass
                f.seek(start_pos + box_size, os.SEEK_SET)
                continue

            # Normal: rewind to start and fully parse
            f.seek(start_pos, os.SEEK_SET)
            box = _parse_box(f, file_size)
            if not box:
                # Ensure forward progress to avoid infinite loop on malformed input
                f.seek(start_pos + max(header_len, 1), os.SEEK_SET)
                continue
            boxes.append(box)

    return boxes


def parse_mp4_boxes(file_path: str) -> List["MP4Box"]:
    """
    Parse all top-level boxes from an MP4 file.

    Uses the streaming parser for large files (>100MB), otherwise the standard parser.
    """
    file_size = os.path.getsize(file_path)

    if file_size > 100 * 1024 * 1024:  # > 100MB
        return parse_mp4_boxes_streaming(file_path)

    boxes: List["MP4Box"] = []
    TrackFragmentBox.reset_counters()
    with open(file_path, "rb") as f:
        while f.tell() < file_size:
            start_pos = f.tell()
            box = _parse_box(f, file_size)
            if not box:
                # Forward progress guard
                hdr = _read_box_header(f, file_size)
                if hdr is None:
                    break
                _, _, header_len, _ = hdr
                f.seek(start_pos + max(header_len, 1), os.SEEK_SET)
                continue
            boxes.append(box)
    return boxes
