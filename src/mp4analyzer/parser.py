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


def _read_u64(f: BinaryIO) -> int:
    """Read big-endian uint64."""
    data = f.read(8)
    if len(data) != 8:
        raise EOFError("Unexpected EOF")
    return struct.unpack(">Q", data)[0]


def _parse_box(
    f: BinaryIO, file_size: int, parent_end: int | None = None, stream_offset: int = 0
) -> MP4Box | None:
    """Parse one box from file or memory."""
    start = stream_offset + f.tell()
    if parent_end and start >= parent_end:
        return None

    header = f.read(8)
    if len(header) < 8:
        return None
    size, btype = struct.unpack(">I4s", header)
    btype = btype.decode("ascii")
    hdr_size = 8

    if size == 1:  # 64-bit size
        size, hdr_size = _read_u64(f), 16
    elif size == 0:  # extends to EOF/parent
        size = (parent_end or file_size) - start

    payload_size, end = size - hdr_size, start + size

    if btype == "mdat":  # skip raw media data
        f.seek(payload_size, os.SEEK_CUR)
        return MediaDataBox(btype, size, start)

    children, data = [], None
    if btype in {"dref", "stsd"}:
        data = f.read(min(8, payload_size))
        while f.tell() + stream_offset < end:
            child = _parse_box(f, file_size, end, stream_offset)
            if not child:
                break
            children.append(child)
    elif btype == "meta":
        import io

        payload = f.read(payload_size)
        header = payload[:4]
        substream = io.BytesIO(payload[4:])
        sub_offset = start + hdr_size + 4
        sub_size = len(payload) - 4
        sub_end = sub_offset + sub_size
        while substream.tell() + sub_offset < sub_end:
            child = _parse_box(
                substream,
                sub_end,
                sub_end,
                sub_offset,
            )
            if not child:
                break
            children.append(child)
        data = payload
    elif btype == "tref":
        import io

        payload = f.read(payload_size)
        substream = io.BytesIO(payload)
        sub_offset = start + hdr_size
        sub_end = sub_offset + len(payload)
        while substream.tell() + sub_offset < sub_end:
            child = _parse_box(
                substream,
                sub_end,
                sub_end,
                sub_offset,
            )
            if not child:
                break
            children.append(child)
        data = payload
    elif btype in CONTAINER_BOX_TYPES and payload_size > 8:
        while f.tell() + stream_offset < end:
            child = _parse_box(f, file_size, end, stream_offset)
            if not child:
                break
            children.append(child)
    else:
        if payload_size > 0 and (btype in BOX_PARSERS or btype in RAW_DATA_BOX_TYPES):
            data = f.read(payload_size)
        else:
            f.seek(payload_size, os.SEEK_CUR)

    box_cls = BOX_PARSERS.get(btype)
    if box_cls and hasattr(box_cls, "from_parsed"):
        return getattr(box_cls, "from_parsed")(
            btype, size, start, data or b"", children
        )
    return MP4Box(btype, size, start, children, data)


def parse_mp4_boxes_streaming(file_path: str, max_memory_mb: int = 50) -> List[MP4Box]:
    """Parse MP4 boxes with memory-conscious streaming for large files."""
    file_size = os.path.getsize(file_path)
    boxes: List[MP4Box] = []
    max_memory_bytes = max_memory_mb * 1024 * 1024
    
    TrackFragmentBox.reset_counters()
    
    with open(file_path, "rb") as f:
        while f.tell() < file_size:
            current_pos = f.tell()
            
            # Peek at box header to check if it's a large mdat
            header = f.read(8)
            if len(header) < 8:
                break
            
            size, btype_bytes = struct.unpack(">I4s", header)
            
            # Handle box type decoding more robustly
            try:
                btype = btype_bytes.decode("ascii")
            except UnicodeDecodeError:
                # Handle non-ASCII box types by using hex representation
                btype = btype_bytes.hex()
                print(f"Warning: Non-ASCII box type encountered: {btype}")
            except Exception:
                # Fallback for any other decoding issues
                btype = "unknown"
            
            # Skip large mdat boxes entirely, just record metadata
            if btype == "mdat" and size > max_memory_bytes:
                box = MediaDataBox(btype, size, current_pos)
                f.seek(size - 8, os.SEEK_CUR)  # Skip payload (we already read 8 bytes)
                boxes.append(box)
                continue
            
            # Reset position and parse normally for smaller boxes
            f.seek(current_pos)
            box = _parse_box(f, file_size)
            if not box:
                break
            boxes.append(box)
            
    return boxes


def parse_mp4_boxes(file_path: str) -> List[MP4Box]:
    """Parse all top-level boxes from an MP4 file."""
    file_size = os.path.getsize(file_path)
    
    # Use streaming parser for large files
    if file_size > 100 * 1024 * 1024:  # > 100MB
        return parse_mp4_boxes_streaming(file_path)
    
    # Original implementation for smaller files
    boxes: List[MP4Box] = []
    TrackFragmentBox.reset_counters()
    with open(file_path, "rb") as f:
        while f.tell() < file_size:
            box = _parse_box(f, file_size)
            if not box:
                break
            boxes.append(box)
    return boxes
