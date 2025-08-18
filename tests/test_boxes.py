import os
import sys
import struct
from typing import Dict
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mp4analyzer import parse_mp4_boxes
from src.mp4analyzer.boxes import (
    FreeSpaceBox,
    MediaDataBox,
    FileTypeBox,
    TrackBox,
    MovieHeaderBox,
    MediaHeaderBox,
    TrackHeaderBox,
    ObjectDescriptorBox,
    MovieBox,
    MovieFragmentBox,
    MovieFragmentHeaderBox,
    TrackFragmentBox,
    TrackFragmentHeaderBox,
    MovieExtendsBox,
    MovieExtendsHeaderBox,
    TrackExtendsBox,
    EditBox,
    EditListBox,
    HandlerBox,
    MediaInformationBox,
    MediaBox,
    MetaBox,
    VideoMediaHeaderBox,
    SoundMediaHeaderBox,
    DataInformationBox,
    DataReferenceBox,
    TrackReferenceBox,
    TrackReferenceTypeBox,
    DataEntryUrlBox,
    SampleTableBox,
    SampleDescriptionBox,
    AVCSampleEntry,
    HEVCSampleEntry,
    AV1SampleEntry,
    MP4AudioSampleEntry,
    AC4SampleEntry,
    DAC4Box,
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
    ElementaryStreamDescriptorBox,
    IlstBox,
    ChapterListBox,
    TextSampleEntry,
    GenericMediaHeaderBox,
    GenericMediaInfoBox,
    TextMediaHeaderBox,
)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def mk_box(type4: bytes, payload: bytes) -> bytes:
    """Create a basic size+type+payload box."""
    return struct.pack(">I4s", 8 + len(payload), type4) + payload


# ------------------------------------------------------------------------------
# Unit tests: properties() for individual box types
# ------------------------------------------------------------------------------


def test_box_properties(tmp_path):
    free = FreeSpaceBox("free", 8, 19061, [], b"")
    assert free.properties() == {
        "size": 8,
        "box_name": "FreeSpaceBox",
        "start": 19061,
        "data": "",
    }

    mdat = MediaDataBox("mdat", 17820776, 19069)
    assert mdat.properties() == {
        "size": 17820776,
        "box_name": "MediaDataBox",
        "start": 19069,
    }

    edts = EditBox("edts", 36, 290, [])
    assert edts.properties() == {
        "size": 36,
        "box_name": "EditBox",
        "start": 290,
    }

    elst_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">I", 1)
        + struct.pack(">I", 0)
        + struct.pack(">i", 0)
        + struct.pack(">h", 1)
        + struct.pack(">h", 0)
    )
    elst = EditListBox.from_parsed("elst", 28, 298, elst_payload, [])
    assert elst.properties() == {
        "size": 28,
        "flags": 0,
        "version": 0,
        "box_name": "EditListBox",
        "start": 298,
        "entry_count": 1,
        "entries": [
            {
                "segment_duration": 0,
                "media_time": 0,
                "media_rate_integer": 1,
                "media_rate_fraction": 0,
            }
        ],
    }

    chap_payload = struct.pack(">I", 2)
    chap = TrackReferenceTypeBox.from_parsed("chap", 12, 292, chap_payload, [])
    tref_payload = struct.pack(">I4sI", 12, b"chap", 2)
    tref = TrackReferenceBox.from_parsed("tref", 20, 284, tref_payload, [chap])
    assert tref.properties() == {
        "size": 20,
        "box_name": "TrackReferenceBox",
        "start": 284,
        "data": "0000000c 63686170 00000002",
    }
    assert chap.properties() == {
        "size": 12,
        "box_name": "TrackReferenceTypeBox",
        "start": 292,
        "track_ids": [2],
    }

    hdlr_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + b"\x00\x00\x00\x00"  # pre_defined
        + b"vide"  # handler
        + b"\x00" * 12  # reserved
        + b"L-SMASH Video Handler\x00"
    )
    hdlr = HandlerBox.from_parsed("hdlr", 8 + len(hdlr_payload), 366, hdlr_payload, [])
    assert hdlr.properties() == {
        "size": 8 + len(hdlr_payload),
        "flags": 0,
        "version": 0,
        "box_name": "HandlerBox",
        "start": 366,
        "handler": "vide",
        "name": "L-SMASH Video Handler",
    }

    minf = MediaInformationBox.from_parsed("minf", 12292, 420, b"", [])
    assert minf.properties() == {
        "size": 12292,
        "box_name": "MediaInformationBox",
        "start": 420,
    }

    vmhd_payload = (
        b"\x00\x00\x00\x01"  # version/flags
        + b"\x00\x00"  # graphicsmode
        + b"\x00\x00\x00\x00\x00\x00"  # opcolor
    )
    vmhd = VideoMediaHeaderBox.from_parsed("vmhd", 20, 428, vmhd_payload, [])
    assert vmhd.properties() == {
        "size": 20,
        "flags": 1,
        "version": 0,
        "box_name": "VideoMediaHeaderBox",
        "start": 428,
        "graphicsmode": 0,
        "opcolor": [0, 0, 0],
    }

    smhd_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + b"\x00\x00"  # balance
        + b"\x00\x00"  # reserved
    )
    smhd = SoundMediaHeaderBox.from_parsed("smhd", 16, 12950, smhd_payload, [])
    assert smhd.properties() == {
        "size": 16,
        "flags": 0,
        "version": 0,
        "box_name": "SoundMediaHeaderBox",
        "start": 12950,
        "balance": 0,
    }

    moof = MovieFragmentBox.from_parsed("moof", 304, 1148, b"", [])
    assert moof.properties() == {
        "size": 304,
        "box_name": "MovieFragmentBox",
        "start": 1148,
    }

    mfhd_payload = b"\x00\x00\x00\x00" + struct.pack(">I", 1)
    mfhd = MovieFragmentHeaderBox.from_parsed("mfhd", 16, 1156, mfhd_payload, [])
    assert mfhd.properties() == {
        "size": 16,
        "flags": 0,
        "version": 0,
        "box_name": "MovieFragmentHeaderBox",
        "start": 1156,
        "sequence_number": 1,
    }

    dinf = DataInformationBox.from_parsed("dinf", 36, 448, b"", [])
    assert dinf.properties() == {
        "size": 36,
        "box_name": "DataInformationBox",
        "start": 448,
    }

    dref_payload = b"\x00\x00\x00\x00" + struct.pack(">I", 1)
    dref = DataReferenceBox.from_parsed("dref", 28, 456, dref_payload, [])
    assert dref.properties() == {
        "size": 28,
        "flags": 0,
        "version": 0,
        "box_name": "DataReferenceBox",
        "start": 456,
    }

    url_payload = b"\x00\x00\x00\x01"
    url = DataEntryUrlBox.from_parsed("url ", 12, 472, url_payload, [])
    assert url.properties() == {
        "size": 12,
        "flags": 1,
        "version": 0,
        "box_name": "DataEntryUrlBox",
        "start": 472,
    }

    stbl = SampleTableBox("stbl", 12228, 484, [])
    assert stbl.properties() == {
        "size": 12228,
        "box_name": "SampleTableBox",
        "start": 484,
    }

    stsd_payload = b"\x00\x00\x00\x00" + struct.pack(">I", 1)
    stsd = SampleDescriptionBox.from_parsed(
        "stsd", 8 + len(stsd_payload), 492, stsd_payload, []
    )
    assert stsd.properties() == {
        "size": 8 + len(stsd_payload),
        "flags": 0,
        "version": 0,
        "entry_count": 1,
        "box_name": "SampleDescriptionBox",
        "start": 492,
    }

    mdia = MediaBox.from_parsed("mdia", 4932, 1264682, b"", [])
    assert mdia.properties() == {
        "size": 4932,
        "box_name": "MediaBox",
        "start": 1264682,
    }

    udta = UserDataBox.from_parsed("udta", 97, 1269614, b"", [])
    assert udta.properties() == {
        "size": 97,
        "box_name": "UserDataBox",
        "start": 1269614,
    }

    meta_payload_hex = (
        "00000021 68646c72 00000000 00000000 6d646972 6170706c "
        "00000000 00000000 00000000 2c696c73 74000000 24a9746f "
        "6f000000 1c646174 61000000 01000000 004c6176 6635392e "
        "322e3130 31"
    )
    meta_payload = bytes.fromhex(meta_payload_hex.replace(" ", ""))
    meta_box = mk_box(b"meta", b"\x00\x00\x00\x00" + meta_payload)
    mp4_path = tmp_path / "meta.mp4"
    mp4_path.write_bytes(meta_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    meta = boxes[0]
    assert isinstance(meta, MetaBox)
    assert [child.type for child in meta.children] == ["hdlr", "ilst"]
    meta_props = meta.properties()
    assert meta_props["size"] == 89
    assert meta_props["flags"] == 0
    assert meta_props["version"] == 0
    assert meta_props["data"] == meta_payload_hex.strip()

    ilst = meta.children[1]
    assert isinstance(ilst, IlstBox)
    expected_hex = (
        "00000024 a9746f6f 0000001c 64617461 00000001 00000000 "
        "4c617666 35392e32 2e313031"
    )
    payload_bytes = b"\x00\x00\x00\x01\x00\x00\x00\x00Lavf59.2.101"
    expected_props = {
        "size": 44,
        "box_name": "IlstBox",
        "start": ilst.offset,
        "data": expected_hex,
        "list": {
            str(0xA9746F6F): {
                "size": 28,
                "box_name": "DataBox",
                "hdr_size": 8,
                "start": ilst.offset + 16,
                "data": {str(i): b for i, b in enumerate(payload_bytes)},
                "valueType": 1,
                "country": 0,
                "language": 0,
                "raw": {str(i): b for i, b in enumerate(b"Lavf59.2.101")},
                "value": "Lavf59.2.101",
            }
        },
    }
    assert ilst.properties() == expected_props


def test_file_type_box_properties():
    data = b"isom" + struct.pack(">I", 512) + b"isomiso2"
    ftyp = FileTypeBox.from_parsed("ftyp", 24, 0, data, [])
    assert ftyp.properties() == {
        "size": 24,
        "box_name": "FileTypeBox",
        "start": 0,
        "major_brand": "isom",
        "minor_version": 512,
        "compatible_brands": ["isom", "iso2"],
    }


def test_colour_information_box_properties():
    payload = b"nclx" + struct.pack(">HHH", 1, 1, 1) + b"\x00"
    colr = ColourInformationBox.from_parsed("colr", 8 + len(payload), 652, payload, [])
    assert colr.properties() == {
        "size": 8 + len(payload),
        "box_name": "ColourInformationBox",
        "start": 652,
        "data": "6e636c78 00010001 000100",
        "colour_type": "nclx",
        "colour_primaries": 1,
        "transfer_characteristics": 1,
        "matrix_coefficients": 1,
        "full_range_flag": 0,
    }


def test_pixel_aspect_ratio_box_properties():
    payload = struct.pack(">II", 1, 1)
    pasp = PixelAspectRatioBox.from_parsed("pasp", 16, 671, payload, [])
    assert pasp.properties() == {
        "size": 16,
        "box_name": "PixelAspectRatioBox",
        "start": 671,
        "data": "00000001 00000001",
        "hSpacing": 1,
        "vSpacing": 1,
    }


def test_field_handling_box_properties():
    payload = b"\x01\x00"
    fiel = FieldHandlingBox.from_parsed("fiel", 10, 2576, payload, [])
    assert fiel.properties() == {
        "size": 10,
        "box_name": "FieldHandlingBox",
        "start": 2576,
        "data": "0100",
        "fieldCount": 1,
        "fieldOrdering": 0,
    }


def test_chapter_list_box_properties():
    payload = (
        b"\x01\x00\x00\x00"  # version/flags
        + struct.pack(">I", 1)  # entry count
        + struct.pack(">I", 0)  # start time
        + struct.pack(">I", 0)  # duration
        + b"\x05Intro"  # name length + name
    )
    chpl = ChapterListBox.from_parsed("chpl", 8 + len(payload), 0, payload, [])
    assert chpl.properties() == {
        "size": 8 + len(payload),
        "box_name": "ChapterListBox",
        "start": 0,
        "version": 1,
        "flags": 0,
        "chapters": [{"start_time": 0, "duration": 0, "title": "Intro"}],
    }


def test_text_sample_entry_properties():
    payload = b"\x00" * 6 + b"\x00\x01" + b"\x00\x00\x00\x01"
    text = TextSampleEntry.from_parsed("text", 8 + len(payload), 0, payload, [])
    assert text.properties() == {
        "size": 8 + len(payload),
        "box_name": "TextSampleEntry",
        "start": 0,
        "data_reference_index": 1,
        "data": "00000001",
    }


def test_generic_media_header_box_parsing():
    gmin_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">H", 64)
        + struct.pack(">HHH", 0x8000, 0x8000, 0)
        + struct.pack(">HH", 0, 0)
    )
    gmin_box = struct.pack(">I4s", 8 + len(gmin_payload), b"gmin") + gmin_payload

    text_payload = (
        b"\x00\x00\x00\x00" + struct.pack(">I", 1) + struct.pack(">I", 0) + b"\x00" * 20
    )
    text_box = struct.pack(">I4s", 8 + len(text_payload), b"text") + text_payload

    gmhd_payload = gmin_box + text_box
    gmhd = GenericMediaHeaderBox.from_parsed(
        "gmhd", 8 + len(gmhd_payload), 0, gmhd_payload, []
    )
    assert gmhd.properties() == {
        "size": 8 + len(gmhd_payload),
        "box_name": "GenericMediaHeaderBox",
        "start": 0,
    }
    assert isinstance(gmhd.children[0], GenericMediaInfoBox)
    assert gmhd.children[0].properties()["graphics_mode"] == 64
    assert isinstance(gmhd.children[1], TextMediaHeaderBox)
    assert gmhd.children[1].properties()["display_flags"] == 1


def test_hevc_configuration_box_properties():
    vps = bytes(
        [
            64,
            1,
            12,
            1,
            255,
            255,
            1,
            64,
            0,
            0,
            3,
            0,
            128,
            0,
            0,
            3,
            0,
            0,
            3,
            0,
            90,
            20,
            144,
            48,
            0,
            20,
            88,
            80,
            4,
            196,
            180,
            5,
        ]
    )
    sps = bytes(
        [
            66,
            1,
            1,
            1,
            64,
            0,
            0,
            3,
            0,
            128,
            0,
            0,
            3,
            0,
            0,
            3,
            0,
            90,
            160,
            5,
            2,
            1,
            113,
            242,
            228,
            20,
            155,
            145,
            176,
            18,
            137,
            232,
            70,
            186,
            111,
            203,
            143,
            94,
            98,
            118,
            68,
            230,
            88,
            251,
            1,
            64,
            40,
            0,
            10,
            44,
            40,
            2,
            98,
            90,
            3,
            0,
            175,
            123,
            240,
            0,
            122,
            18,
            0,
            15,
            66,
            100,
        ]
    )
    pps = bytes([68, 1, 192, 60, 54, 3, 108, 128, 0])

    hvcc_payload = (
        b"\x01"  # configurationVersion
        + b"\x01"  # profile/tier/idc
        + b"\x40\x00\x00\x00"  # general_profile_compatibility
        + bytes([128, 0, 0, 0, 0, 0])  # general_constraint_indicator
        + b"\x5a"  # general_level_idc
        + b"\xf0\x00"  # min_spatial_segmentation_idc
        + b"\xfc"  # parallelismType
        + b"\xfd"  # chroma_format_idc
        + b"\xf8"  # bit_depth_luma_minus8
        + b"\xf8"  # bit_depth_chroma_minus8
        + b"\x00\x00"  # avgFrameRate
        + b"\x0f"  # constantFrameRate/numTemporalLayers/temporalIdNested/lengthSizeMinusOne
        + b"\x03"  # numOfArrays
        + b"\xa0\x00\x01\x00\x20"
        + vps
        + b"\xa1\x00\x01\x00\x42"
        + sps
        + b"\xa2\x00\x01\x00\x09"
        + pps
    )
    hvcc = HEVCConfigurationBox.from_parsed(
        "hvcC", 8 + len(hvcc_payload), 1264941, hvcc_payload, []
    )

    def bdict(b: bytes) -> Dict[str, int]:
        return {str(i): v for i, v in enumerate(b)}

    assert hvcc.properties() == {
        "size": 8 + len(hvcc_payload),
        "box_name": "HEVCConfigurationBox",
        "start": 1264941,
        "configurationVersion": 1,
        "general_profile_space": 0,
        "general_tier_flag": 0,
        "general_profile_idc": 1,
        "general_profile_compatibility": 1073741824,
        "general_constraint_indicator": [128, 0, 0, 0, 0, 0],
        "general_level_idc": 90,
        "min_spatial_segmentation_idc": 0,
        "parallelismType": 0,
        "chroma_format_idc": 1,
        "bit_depth_luma_minus8": 0,
        "bit_depth_chroma_minus8": 0,
        "avgFrameRate": 0,
        "constantFrameRate": 0,
        "numTemporalLayers": 1,
        "temporalIdNested": 1,
        "lengthSizeMinusOne": 3,
        "nalu_arrays": [
            [{"data": bdict(vps)}],
            [{"data": bdict(sps)}],
            [{"data": bdict(pps)}],
        ],
    }


def test_bit_rate_box_properties():
    payload = struct.pack(">III", 0, 0x000F6F5D, 0x000F6F5D)
    btrt = BitRateBox.from_parsed("btrt", 20, 1265110, payload, [])
    assert btrt.properties() == {
        "size": 20,
        "box_name": "BitRateBox",
        "start": 1265110,
        "data": "00000000 000f6f5d 000f6f5d",
        "bufferSizeDB": 0,
        "maxBitrate": 1011549,
        "avgBitrate": 1011549,
    }


def test_movie_header_box_properties():
    matrix = [0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000]
    payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">IIII", 1, 2, 1000, 5000)
        + struct.pack(">I", 0x00010000)  # rate
        + struct.pack(">H", 0x0100)  # volume
        + b"\x00" * 10  # reserved
        + b"".join(struct.pack(">I", v) for v in matrix)
        + b"\x00" * 24  # pre-defined
        + struct.pack(">I", 5)  # next_track_id
    )
    mvhd = MovieHeaderBox.from_parsed("mvhd", 8 + len(payload), 0, payload, [])
    props = mvhd.properties()
    assert props == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "MovieHeaderBox",
        "start": 0,
        "creation_time": 1,
        "modification_time": 2,
        "timescale": 1000,
        "duration": 5000,
        "rate": 0x00010000,
        "volume": pytest.approx(1.0),
        "matrix": matrix,
        "next_track_id": 5,
    }


def test_media_header_box_properties():
    payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">IIII", 3521783616, 3521783616, 30, 901)
        + struct.pack(">HH", 21956, 0)
    )
    mdhd = MediaHeaderBox.from_parsed("mdhd", 32, 334, payload, [])
    assert mdhd.properties() == {
        "size": 32,
        "flags": 0,
        "version": 0,
        "box_name": "MediaHeaderBox",
        "start": 334,
        "creation_time": 3521783616,
        "modification_time": 3521783616,
        "timescale": 30,
        "duration": 901,
        "language": 21956,
        "languageString": "und",
    }


def test_track_header_box_properties():
    matrix = [0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000]
    payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">I", 1)  # creation_time
        + struct.pack(">I", 2)  # modification_time
        + struct.pack(">I", 3)  # track_id
        + b"\x00\x00\x00\x00"  # reserved
        + struct.pack(">I", 400)  # duration
        + b"\x00" * 8  # reserved
        + struct.pack(">h", 0)  # layer
        + struct.pack(">h", 0)  # alternate_group
        + struct.pack(">H", 0x0100)  # volume
        + b"\x00\x00"  # reserved
        + b"".join(struct.pack(">I", v) for v in matrix)
        + struct.pack(">I", 0x00010000)  # width
        + struct.pack(">I", 0x00020000)  # height
    )
    tkhd = TrackHeaderBox.from_parsed("tkhd", 8 + len(payload), 0, payload, [])
    props = tkhd.properties()
    assert props == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "TrackHeaderBox",
        "layer": 0,
        "alternate_group": 0,
        "start": 0,
        "creation_time": 1,
        "modification_time": 2,
        "track_id": 3,
        "duration": 400,
        "volume": pytest.approx(1.0),
        "matrix": matrix,
        "width": 0x00010000,
        "height": 0x00020000,
    }


def test_object_descriptor_box_properties():
    descriptor = b"\x11\x22\x33"
    payload = b"\x00\x00\x00\x00" + descriptor
    iods = ObjectDescriptorBox.from_parsed("iods", 8 + len(payload), 0, payload, [])
    assert iods.properties() == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "ObjectDescriptorBox",
        "start": 0,
        "data": "112233",
    }


def test_avc_configuration_box_properties():
    avcc_payload = (
        b"\x01"  # configurationVersion
        + b"\x64"  # AVCProfileIndication
        + b"\x00"  # profile_compatibility
        + b"\x28"  # AVCLevelIndication
        + b"\xff"  # lengthSizeMinusOne (6 bits reserved)
        + b"\xe1"  # numOfSequenceParameterSets (3 bits reserved)
        + struct.pack(">H", 30)  # SPS length
        + bytes.fromhex(
            "67640028acd940780227e5c05a808080a0000003002000000781e30632c0"
        )  # SPS NALU
        + b"\x01"  # numOfPictureParameterSets
        + struct.pack(">H", 5)  # PPS length
        + bytes.fromhex("68e93b2c8b")  # PPS NALU
        + bytes([253, 248, 248, 0])  # ext
    )
    avcc = AVCConfigurationBox.from_parsed("avcC", 58, 594, avcc_payload, [])
    assert avcc.properties() == {
        "size": 58,
        "box_name": "AVCConfigurationBox",
        "start": 594,
        "configurationVersion": 1,
        "AVCProfileIndication": 100,
        "profile_compatibility": 0,
        "AVCLevelIndication": 40,
        "lengthSizeMinusOne": 3,
        "nb_SPS_nalus": 1,
        "SPS": [
            {
                "length": 30,
                "nalu_data": "0x"
                "67640028acd940780227e5c05a808080a0000003002000000781e30632c0",
            }
        ],
        "nb_PPS_nalus": 1,
        "PPS": [
            {"length": 5, "nalu_data": "0x68e93b2c8b"},
        ],
        "ext": [253, 248, 248, 0],
    }


def test_avc_sample_entry_properties():
    avcc_payload = (
        b"\x01"
        + b"\x64"
        + b"\x00"
        + b"\x28"
        + b"\xff"
        + b"\xe1"
        + struct.pack(">H", 30)
        + bytes.fromhex("67640028acd940780227e5c05a808080a0000003002000000781e30632c0")
        + b"\x01"
        + struct.pack(">H", 5)
        + bytes.fromhex("68e93b2c8b")
        + bytes([253, 248, 248, 0])
    )
    avcc_box = mk_box(b"avcC", avcc_payload)

    # Build the avc1 header (78 bytes) followed by avcC box and fiel boxes
    name = b"AVC Coding"
    compressor_field = bytes([len(name)]) + name + b"\x00" * (31 - len(name))
    header = (
        b"\x00" * 6
        + struct.pack(">H", 1)  # data_reference_index
        + b"\x00" * 16
        + struct.pack(">H", 1920)
        + struct.pack(">H", 1080)
        + struct.pack(">I", 4718592)
        + struct.pack(">I", 4718592)
        + b"\x00" * 4
        + struct.pack(">H", 1)  # frame_count
        + compressor_field
        + struct.pack(">H", 0)  # depth
        + b"\xff\xff"  # pre_defined
    )
    fiel_payload = b"\x01\x00"
    fiel_box = mk_box(b"fiel", fiel_payload)
    avc1_payload = header + avcc_box + fiel_box
    avc1_size = 8 + len(avc1_payload)
    avc1 = AVCSampleEntry.from_parsed("avc1", avc1_size, 508, avc1_payload, [])
    assert avc1.properties() == {
        "size": avc1_size,
        "box_name": "AVCSampleEntry",
        "start": 508,
        "data_reference_index": 1,
        "width": 1920,
        "height": 1080,
        "horizresolution": 4718592,
        "vertresolution": 4718592,
        "frame_count": 1,
        "compressorname": "AVC Coding",
        "depth": 0,
    }
    assert len(avc1.children) == 2
    assert isinstance(avc1.children[0], AVCConfigurationBox)
    assert isinstance(avc1.children[1], FieldHandlingBox)

    comp_field = b"\x00" * 32
    header = (
        b"\x00" * 6
        + struct.pack(">H", 1)
        + b"\x00" * 16
        + struct.pack(">H", 640)
        + struct.pack(">H", 360)
        + struct.pack(">I", 4718592)
        + struct.pack(">I", 4718592)
        + b"\x00" * 4
        + struct.pack(">H", 1)
        + comp_field
        + struct.pack(">H", 24)
        + b"\xff\xff"
    )
    hvcc_box = mk_box(b"hvcC", b"")
    btrt_payload = struct.pack(">III", 0, 0x000F6F5D, 0x000F6F5D)
    btrt_box = mk_box(b"btrt", btrt_payload)
    pasp_payload = struct.pack(">II", 1, 1)
    pasp_box = mk_box(b"pasp", pasp_payload)
    fiel_payload = b"\x01\x00"
    fiel_box = mk_box(b"fiel", fiel_payload)
    hev1_payload = header + hvcc_box + btrt_box + fiel_box + pasp_box
    hev1_size = 8 + len(hev1_payload)
    hev1 = HEVCSampleEntry.from_parsed("hev1", hev1_size, 1264855, hev1_payload, [])
    assert hev1.properties() == {
        "size": hev1_size,
        "box_name": "HEVCSampleEntry",
        "start": 1264855,
        "data_reference_index": 1,
        "width": 640,
        "height": 360,
        "horizresolution": 4718592,
        "vertresolution": 4718592,
        "frame_count": 1,
        "compressorname": "",
        "depth": 24,
    }
    assert len(hev1.children) == 4
    assert isinstance(hev1.children[0], HEVCConfigurationBox)
    assert isinstance(hev1.children[1], BitRateBox)
    assert isinstance(hev1.children[2], FieldHandlingBox)
    assert isinstance(hev1.children[3], PixelAspectRatioBox)
    mp4a_payload = (
        b"\x00" * 6
        + struct.pack(">H", 1)  # data_reference_index
        + struct.pack(">H", 0)  # version
        + b"\x00\x00"  # revision level
        + b"\x00\x00\x00\x00"  # vendor
        + struct.pack(">H", 2)  # channel_count
        + struct.pack(">H", 16)  # samplesize
        + b"\x00\x00"  # pre_defined
        + b"\x00\x00"  # reserved
        + struct.pack(">I", 48000 << 16)  # samplerate
    )
    mp4a = MP4AudioSampleEntry.from_parsed(
        "mp4a", 8 + len(mp4a_payload), 13026, mp4a_payload, []
    )
    assert mp4a.properties() == {
        "size": 8 + len(mp4a_payload),
        "box_name": "MP4AudioSampleEntry",
        "start": 13026,
        "data_reference_index": 1,
        "version": 0,
        "channel_count": 2,
        "samplesize": 16,
        "samplerate": 48000,
    }


def test_ac4_sample_entry_properties():
    ac4_header = (
        b"\x00" * 6
        + struct.pack(">H", 1)
        + struct.pack(">H", 0)
        + b"\x00\x00"
        + b"\x00\x00\x00\x00"
        + struct.pack(">H", 2)
        + struct.pack(">H", 16)
        + b"\x00\x00"
        + b"\x00\x00"
        + struct.pack(">I", 48000 << 16)
    )
    dac4_payload = bytes.fromhex(
        "20a40140 0000001f ffffffe0 010ff880 00004200 00025010 00000300 80".replace(
            " ", ""
        )
    )
    dac4_box = struct.pack(">I4s", 8 + len(dac4_payload), b"dac4") + dac4_payload
    ac4_payload = ac4_header + dac4_box
    ac4 = AC4SampleEntry.from_parsed("ac-4", 8 + len(ac4_payload), 425, ac4_payload, [])
    assert ac4.properties() == {
        "size": 8 + len(ac4_payload),
        "box_name": "AC4SampleEntry",
        "start": 425,
        "data_reference_index": 1,
        "version": 0,
        "channel_count": 2,
        "samplesize": 16,
        "samplerate": 48000,
    }
    assert len(ac4.children) == 1
    dac4 = ac4.children[0]
    assert isinstance(dac4, DAC4Box)
    assert dac4.properties() == {
        "size": 8 + len(dac4_payload),
        "box_name": "DAC4Box",
        "start": 461,
        "has_unparsed_data": True,
        "data": "20a40140 0000001f ffffffe0 010ff880 00004200 00025010 00000300 80",
    }


def test_av1_codec_configuration_box_properties():
    payload = bytes([0x81, 0x2A, 0xCA, 0x15, 0x01, 0x02, 0x03])
    av1c = AV1CodecConfigurationBox.from_parsed(
        "av1C", 8 + len(payload), 500, payload, []
    )
    assert av1c.properties() == {
        "size": 8 + len(payload),
        "box_name": "AV1CodecConfigurationBox",
        "start": 500,
        "configurationVersion": 1,
        "seq_profile": 1,
        "seq_level_idx_0": 10,
        "seq_tier_0": 1,
        "high_bitdepth": 1,
        "twelve_bit": 0,
        "monochrome": 0,
        "chroma_subsampling_x": 1,
        "chroma_subsampling_y": 0,
        "chroma_sample_position": 2,
        "initial_presentation_delay_present": 1,
        "initial_presentation_delay_minus_one": 5,
        "configOBUs": [1, 2, 3],
    }


def test_av1_sample_entry_properties():
    av1c_payload = bytes([0x81, 0x2A, 0xCA, 0x15, 0x01, 0x02, 0x03])
    av1c_box = mk_box(b"av1C", av1c_payload)

    name = b"AV1 Coding"
    compressor_field = bytes([len(name)]) + name + b"\x00" * (31 - len(name))
    header = (
        b"\x00" * 6
        + struct.pack(">H", 1)  # data_reference_index
        + b"\x00" * 16
        + struct.pack(">H", 1280)
        + struct.pack(">H", 720)
        + struct.pack(">I", 4718592)
        + struct.pack(">I", 4718592)
        + b"\x00" * 4
        + struct.pack(">H", 1)  # frame_count
        + compressor_field
        + struct.pack(">H", 24)  # depth
        + b"\xff\xff"
    )
    fiel_payload = b"\x01\x00"
    fiel_box = mk_box(b"fiel", fiel_payload)
    av01_payload = header + av1c_box + fiel_box
    av01_size = 8 + len(av01_payload)
    av01 = AV1SampleEntry.from_parsed("av01", av01_size, 2000, av01_payload, [])
    assert av01.properties() == {
        "size": av01_size,
        "box_name": "AV1SampleEntry",
        "start": 2000,
        "data_reference_index": 1,
        "width": 1280,
        "height": 720,
        "horizresolution": 4718592,
        "vertresolution": 4718592,
        "frame_count": 1,
        "compressorname": "AV1 Coding",
        "depth": 24,
    }
    assert len(av01.children) == 2
    assert isinstance(av01.children[0], AV1CodecConfigurationBox)
    assert isinstance(av01.children[1], FieldHandlingBox)


def test_movie_extends_header_box_properties():
    payload = b"\x00\x00\x00\x00" + struct.pack(">I", 32000)
    mehd = MovieExtendsHeaderBox.from_parsed("mehd", 16, 1068, payload, [])
    assert mehd.properties() == {
        "size": 16,
        "flags": 0,
        "version": 0,
        "box_name": "MovieExtendsHeaderBox",
        "start": 1068,
        "fragment_duration": 32000,
    }


def test_track_extends_box_properties():
    payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">I", 1)
        + struct.pack(">I", 1)
        + struct.pack(">I", 0)
        + struct.pack(">I", 0)
        + struct.pack(">I", 0)
    )
    trex = TrackExtendsBox.from_parsed("trex", 32, 1084, payload, [])
    assert trex.properties() == {
        "size": 32,
        "flags": 0,
        "version": 0,
        "box_name": "TrackExtendsBox",
        "start": 1084,
        "track_id": 1,
        "default_sample_description_index": 1,
        "default_sample_duration": 0,
        "default_sample_size": 0,
        "default_sample_flags": 0,
    }


# ------------------------------------------------------------------------------
# Small integration tests: parse synthetic MP4 fragments
# ------------------------------------------------------------------------------


def test_parse_free_and_mdat(tmp_path):
    mp4_path = tmp_path / "simple.mp4"
    with open(mp4_path, "wb") as f:
        # free box (size 8)
        f.write(struct.pack(">I4s", 8, b"free"))
        # mdat box (size 16, 8 bytes payload)
        f.write(struct.pack(">I4s", 16, b"mdat"))
        f.write(b"\x00" * 8)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert [box.type for box in boxes] == ["free", "mdat"]
    assert isinstance(boxes[0], FreeSpaceBox)
    assert isinstance(boxes[1], MediaDataBox)


def test_movie_box_parsing(tmp_path):
    matrix = [0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000]
    mvhd_payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">IIII", 1, 2, 1000, 5000)
        + struct.pack(">I", 0x00010000)
        + struct.pack(">H", 0x0100)
        + b"\x00" * 10
        + b"".join(struct.pack(">I", v) for v in matrix)
        + b"\x00" * 24
        + struct.pack(">I", 5)
    )
    mvhd_box = mk_box(b"mvhd", mvhd_payload)
    moov_box = mk_box(b"moov", mvhd_box)

    mp4_path = tmp_path / "movie.mp4"
    mp4_path.write_bytes(moov_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1

    moov = boxes[0]
    assert isinstance(moov, MovieBox)
    assert len(moov.children) == 1
    assert isinstance(moov.children[0], MovieHeaderBox)
    assert moov.properties() == {
        "size": len(moov_box),
        "box_name": "MovieBox",
        "start": 0,
    }


def test_movie_extends_box(tmp_path):
    mehd_payload = b"\x00\x00\x00\x00" + struct.pack(">I", 32000)
    mehd_box = mk_box(b"mehd", mehd_payload)
    trex_payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">I", 1)
        + struct.pack(">I", 1)
        + struct.pack(">I", 0)
        + struct.pack(">I", 0)
        + struct.pack(">I", 0)
    )
    trex_box = mk_box(b"trex", trex_payload)
    mvex_box = mk_box(b"mvex", mehd_box + trex_box)

    mp4_path = tmp_path / "mvex.mp4"
    mp4_path.write_bytes(mvex_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1

    mvex = boxes[0]
    assert isinstance(mvex, MovieExtendsBox)
    assert len(mvex.children) == 2
    mehd = mvex.children[0]
    trex = mvex.children[1]
    assert isinstance(mehd, MovieExtendsHeaderBox)
    assert isinstance(trex, TrackExtendsBox)
    assert mehd.properties() == {
        "size": len(mehd_box),
        "flags": 0,
        "version": 0,
        "box_name": "MovieExtendsHeaderBox",
        "start": 8,
        "fragment_duration": 32000,
    }
    assert trex.properties() == {
        "size": len(trex_box),
        "flags": 0,
        "version": 0,
        "box_name": "TrackExtendsBox",
        "start": 24,
        "track_id": 1,
        "default_sample_description_index": 1,
        "default_sample_duration": 0,
        "default_sample_size": 0,
        "default_sample_flags": 0,
    }
    assert mvex.properties() == {
        "size": len(mvex_box),
        "box_name": "MovieExtendsBox",
        "start": 0,
    }


def test_movie_fragment_box(tmp_path):
    mfhd_payload = b"\x00\x00\x00\x00" + struct.pack(">I", 1)
    mfhd_box = mk_box(b"mfhd", mfhd_payload)
    moof_box = mk_box(b"moof", mfhd_box)

    mp4_path = tmp_path / "moof.mp4"
    mp4_path.write_bytes(moof_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1

    moof = boxes[0]
    assert isinstance(moof, MovieFragmentBox)
    assert len(moof.children) == 1
    mfhd = moof.children[0]
    assert isinstance(mfhd, MovieFragmentHeaderBox)
    assert mfhd.properties() == {
        "size": len(mfhd_box),
        "flags": 0,
        "version": 0,
        "box_name": "MovieFragmentHeaderBox",
        "start": 8,
        "sequence_number": 1,
    }
    assert moof.properties() == {
        "size": len(moof_box),
        "box_name": "MovieFragmentBox",
        "start": 0,
    }


def test_track_fragment_and_header_boxes(tmp_path):
    tfhd_payload = (
        b"\x00"  # version
        + (131114).to_bytes(3, "big")  # flags 0x2002A
        + struct.pack(">I", 2)  # track_id
        + struct.pack(">I", 1)  # default_sample_description_index
        + struct.pack(">I", 1000)  # default_sample_duration
        + struct.pack(">I", 16842752)  # default_sample_flags
    )
    tfhd_box1 = mk_box(b"tfhd", tfhd_payload)
    trun_box1 = mk_box(b"trun", b"\x00\x00\x00\x00" + struct.pack(">I", 798))
    traf_box1 = mk_box(b"traf", tfhd_box1 + trun_box1)

    tfhd_box2 = mk_box(b"tfhd", tfhd_payload)
    trun_box2 = mk_box(b"trun", b"\x00\x00\x00\x00" + struct.pack(">I", 25))
    traf_box2 = mk_box(b"traf", tfhd_box2 + trun_box2)

    mfhd_box1 = mk_box(b"mfhd", b"\x00\x00\x00\x00" + struct.pack(">I", 1))
    moof_box1 = mk_box(b"moof", mfhd_box1 + traf_box1)

    mfhd_box2 = mk_box(b"mfhd", b"\x00\x00\x00\x00" + struct.pack(">I", 2))
    moof_box2 = mk_box(b"moof", mfhd_box2 + traf_box2)

    mp4_path = tmp_path / "traf.mp4"
    mp4_path.write_bytes(moof_box1 + moof_box2)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 2
    moof2 = boxes[1]
    assert isinstance(moof2, MovieFragmentBox)
    traf2 = moof2.children[1]
    assert isinstance(traf2, TrackFragmentBox)
    tfhd2 = traf2.children[0]
    assert isinstance(tfhd2, TrackFragmentHeaderBox)

    assert tfhd2.properties() == {
        "size": len(tfhd_box2),
        "flags": 131114,
        "version": 0,
        "box_name": "TrackFragmentHeaderBox",
        "start": tfhd2.offset,
        "track_id": 2,
        "base_data_offset": 0,
        "default_sample_description_index": 1,
        "default_sample_duration": 1000,
        "default_sample_size": 0,
        "default_sample_flags": 16842752,
    }

    assert traf2.properties() == {
        "size": len(traf_box2),
        "box_name": "TrackFragmentBox",
        "start": traf2.offset,
        "sample_number": 25,
        "first_sample_index": 799,
    }


def test_track_box_aggregation(tmp_path):
    # stts (time-to-sample)
    stts_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">I", 1)  # entry count
        + struct.pack(">I", 3)  # sample count
        + struct.pack(">I", 100)  # sample delta
    )
    stts = mk_box(b"stts", stts_payload)

    # stsz (sample sizes)
    stsz_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">I", 0)  # sample size (table form)
        + struct.pack(">I", 3)  # sample count
        + struct.pack(">I", 10)
        + struct.pack(">I", 20)
        + struct.pack(">I", 30)
    )
    stsz = mk_box(b"stsz", stsz_payload)

    # sgpd (sample group description)
    sgpd_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + b"roll"  # grouping type
        + struct.pack(">I", 2)  # entry count
    )
    sgpd = mk_box(b"sgpd", sgpd_payload)

    stbl = mk_box(b"stbl", stts + stsz + sgpd)
    minf = mk_box(b"minf", stbl)
    mdia = mk_box(b"mdia", minf)
    trak = mk_box(b"trak", mdia)

    mp4_path = tmp_path / "track.mp4"
    mp4_path.write_bytes(trak)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    track = boxes[0]
    assert isinstance(track, TrackBox)
    assert track.properties() == {
        "size": len(trak),
        "box_name": "TrackBox",
        "start": 0,
        "samples_duration": 300,
        "samples_size": 60,
        "sample_groups_info": [{"grouping_type": "roll", "entry_count": 2}],
    }


def test_sample_group_boxes(tmp_path):
    sgpd_payload = (
        b"\x01\x00\x00\x00"  # version/flags
        + b"roll"  # grouping type
        + struct.pack(">I", 2)  # default length
        + struct.pack(">I", 0)  # entry count
    )
    sbgp_payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + b"roll"  # grouping type
        + struct.pack(">I", 1)  # entry count
        + struct.pack(">I", 901)
        + struct.pack(">I", 0)
    )
    mp4_path = tmp_path / "groups.mp4"
    mp4_path.write_bytes(mk_box(b"sgpd", sgpd_payload) + mk_box(b"sbgp", sbgp_payload))

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 2
    sgpd, sbgp = boxes
    assert isinstance(sgpd, SampleGroupDescriptionBox)
    assert isinstance(sbgp, SampleToGroupBox)
    assert sgpd.properties() == {
        "size": 24,
        "flags": 0,
        "version": 1,
        "box_name": "SampleGroupDescriptionBox",
        "start": 0,
        "grouping_type": "roll",
        "default_length": 2,
        "used": True,
    }
    assert sbgp.properties() == {
        "size": 28,
        "flags": 0,
        "version": 0,
        "box_name": "SampleToGroupBox",
        "start": 24,
        "grouping_type": "roll",
        "grouping_type_parameter": 0,
        "entries": [{"sample_count": 901, "group_description_index": 0}],
    }


def test_parse_handler_and_minf(tmp_path):
    name = "L-SMASH Video Handler"
    payload = (
        b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"vide"
        + b"\x00" * 12
        + name.encode("utf-8")
        + b"\x00"
    )
    hdlr_box = mk_box(b"hdlr", payload)
    minf_box = mk_box(b"minf", b"")
    mp4_path = tmp_path / "boxes.mp4"
    mp4_path.write_bytes(hdlr_box + minf_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert [box.type for box in boxes] == ["hdlr", "minf"]
    assert isinstance(boxes[0], HandlerBox)
    assert isinstance(boxes[1], MediaInformationBox)


def test_parse_vmhd_and_dinf(tmp_path):
    vmhd_payload = b"\x00\x00\x00\x01" + b"\x00\x00" + b"\x00\x00\x00\x00\x00\x00"
    vmhd_box = mk_box(b"vmhd", vmhd_payload)
    url_payload = b"\x00\x00\x00\x01"
    url_box = mk_box(b"url ", url_payload)
    dref_payload = b"\x00\x00\x00\x00" + struct.pack(">I", 1) + url_box
    dref_box = mk_box(b"dref", dref_payload)
    dinf_box = mk_box(b"dinf", dref_box)
    minf_box = mk_box(b"minf", vmhd_box + dinf_box)

    mp4_path = tmp_path / "vmhd_dinf.mp4"
    mp4_path.write_bytes(minf_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    minf = boxes[0]
    assert isinstance(minf, MediaInformationBox)
    child_types = [type(c) for c in minf.children]
    assert VideoMediaHeaderBox in child_types
    assert DataInformationBox in child_types
    dinf = next(c for c in minf.children if isinstance(c, DataInformationBox))
    dref_types = [type(c) for c in dinf.children]
    assert DataReferenceBox in dref_types
    dref = next(c for c in dinf.children if isinstance(c, DataReferenceBox))
    url_types = [type(c) for c in dref.children]
    assert DataEntryUrlBox in url_types


def test_parse_stsd_in_stbl(tmp_path):
    sample_entry = mk_box(b"mp4a", b"")
    stsd_payload = b"\x00\x00\x00\x00" + struct.pack(">I", 1) + sample_entry
    stsd_box = mk_box(b"stsd", stsd_payload)
    stbl_box = mk_box(b"stbl", stsd_box)
    mp4_path = tmp_path / "stsd.mp4"
    mp4_path.write_bytes(stbl_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    stbl = boxes[0]
    assert isinstance(stbl, SampleTableBox)
    assert len(stbl.children) == 1
    stsd = stbl.children[0]
    assert isinstance(stsd, SampleDescriptionBox)
    assert stsd.entry_count == 1
    assert isinstance(stsd.children[0], MP4AudioSampleEntry)


def test_time_to_sample_box_properties(tmp_path):
    payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">I", 1)
        + struct.pack(">I", 901)
        + struct.pack(">I", 1)
    )
    stts_box = mk_box(b"stts", payload)
    mp4_path = tmp_path / "stts.mp4"
    mp4_path.write_bytes(stts_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    stts = boxes[0]
    assert isinstance(stts, TimeToSampleBox)
    assert stts.properties() == {
        "size": 24,
        "flags": 0,
        "version": 0,
        "box_name": "TimeToSampleBox",
        "start": 0,
        "sample_counts": [901],
        "sample_deltas": [1],
    }


def test_composition_offset_box_properties(tmp_path):
    payload = (
        b"\x00\x00\x00\x00"  # version/flags
        + struct.pack(">I", 2)
        + struct.pack(">I", 1)
        + struct.pack(">I", 2)
        + struct.pack(">I", 2)
        + struct.pack(">I", 5)
    )
    ctts_box = mk_box(b"ctts", payload)
    mp4_path = tmp_path / "ctts.mp4"
    mp4_path.write_bytes(ctts_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    ctts = boxes[0]
    assert isinstance(ctts, CompositionOffsetBox)
    assert ctts.properties() == {
        "size": 32,
        "flags": 0,
        "version": 0,
        "box_name": "CompositionOffsetBox",
        "start": 0,
        "sample_counts": [1, 2],
        "sample_offsets": [2, 5],
    }


def test_sync_sample_box_properties(tmp_path):
    payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">I", 3)
        + struct.pack(">I", 1)
        + struct.pack(">I", 91)
        + struct.pack(">I", 181)
    )
    stss_box = mk_box(b"stss", payload)
    mp4_path = tmp_path / "stss.mp4"
    mp4_path.write_bytes(stss_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    stss = boxes[0]
    assert isinstance(stss, SyncSampleBox)
    assert stss.properties() == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "SyncSampleBox",
        "start": 0,
        "sample_numbers": [1, 91, 181],
    }


def test_sample_dependency_type_box_properties(tmp_path):
    payload = b"\x00\x00\x00\x00" + bytes.fromhex("a6 96 96 9a")
    sdtp_box = mk_box(b"sdtp", payload)
    mp4_path = tmp_path / "sdtp.mp4"
    mp4_path.write_bytes(sdtp_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    sdtp = boxes[0]
    assert isinstance(sdtp, SampleDependencyTypeBox)
    assert sdtp.properties() == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "SampleDependencyTypeBox",
        "start": 0,
        "data": "a696969a",
        "is_leading": [2, 2, 2, 2],
        "sample_depends_on": [2, 1, 1, 1],
        "sample_is_depended_on": [1, 1, 1, 2],
        "sample_has_redundancy": [2, 2, 2, 2],
    }


def test_sample_to_chunk_box_properties(tmp_path):
    payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">I", 2)
        + struct.pack(">III", 1, 31, 1)
        + struct.pack(">III", 30, 2, 1)
    )
    stsc_box = mk_box(b"stsc", payload)
    mp4_path = tmp_path / "stsc.mp4"
    mp4_path.write_bytes(stsc_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    stsc = boxes[0]
    assert isinstance(stsc, SampleToChunkBox)
    assert stsc.properties() == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "SampleToChunkBox",
        "start": 0,
        "first_chunk": [1, 30],
        "samples_per_chunk": [31, 2],
        "sample_description_index": [1, 1],
    }


def test_sample_size_box_properties(tmp_path):
    payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">I", 0)
        + struct.pack(">I", 3)
        + struct.pack(">I", 10)
        + struct.pack(">I", 20)
        + struct.pack(">I", 30)
    )
    stsz_box = mk_box(b"stsz", payload)
    mp4_path = tmp_path / "stsz.mp4"
    mp4_path.write_bytes(stsz_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    stsz = boxes[0]
    assert isinstance(stsz, SampleSizeBox)
    assert stsz.properties() == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "SampleSizeBox",
        "start": 0,
        "sample_sizes": [10, 20, 30],
        "sample_size": 0,
        "sample_count": 3,
    }


def test_chunk_offset_box_properties(tmp_path):
    payload = (
        b"\x00\x00\x00\x00"
        + struct.pack(">I", 3)
        + struct.pack(">I", 19077)
        + struct.pack(">I", 741483)
        + struct.pack(">I", 1235346)
    )
    stco_box = mk_box(b"stco", payload)
    mp4_path = tmp_path / "stco.mp4"
    mp4_path.write_bytes(stco_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    stco = boxes[0]
    assert isinstance(stco, ChunkOffsetBox)
    assert stco.properties() == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "ChunkOffsetBox",
        "start": 0,
        "chunk_offsets": [19077, 741483, 1235346],
    }


def test_esds_box_properties(tmp_path):
    descriptor_hex = (
        "03 80 80 80 22 00 00 00 04 80 80 80 14 40 15 00 02 ab 00 04 "
        "00 00 00 00 00 00 05 80 80 80 02 11 90 06 80 80 80 01 02"
    )
    descriptor = bytes.fromhex(descriptor_hex)
    payload = b"\x00\x00\x00\x00" + descriptor
    esds_box = mk_box(b"esds", payload)
    mp4_path = tmp_path / "esds.mp4"
    mp4_path.write_bytes(esds_box)

    boxes = parse_mp4_boxes(str(mp4_path))
    assert len(boxes) == 1
    esds = boxes[0]
    assert isinstance(esds, ElementaryStreamDescriptorBox)
    assert esds.properties() == {
        "size": 8 + len(payload),
        "flags": 0,
        "version": 0,
        "box_name": "ElementaryStreamDescriptorBox",
        "start": 0,
        "data": "03808080 22000000 04808080 14401500 02ab0004 00000000 00000580 "
        "80800211 90068080 800102",
        "descriptor": {
            "tag": 3,
            "size": 34,
            "ES_ID": 0,
            "flags": 0,
            "dependsOn_ES_ID": 0,
            "URL": "",
            "OCR_ES_ID": 0,
            "decoderConfig": {
                "tag": 4,
                "size": 20,
                "oti": 64,
                "streamType": 5,
                "upStream": False,
                "bufferSize": 683,
                "maxBitrate": 262144,
                "avgBitrate": 0,
                "decSpecificInfo": {"tag": 5, "size": 2, "data": "1190"},
            },
            "slConfig": {"tag": 6, "size": 1, "data": "02"},
        },
    }


# ------------------------------------------------------------------------------
# Variants & edge cases
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "major,minor,brands",
    [
        (b"isom", 512, [b"isom", b"iso2"]),
        (b"mp42", 0, [b"isom", b"mp42"]),
    ],
)
def test_ftyp_variants(major, minor, brands, tmp_path):
    payload = major + struct.pack(">I", minor) + b"".join(brands)
    ftyp = mk_box(b"ftyp", payload)

    p = tmp_path / "a.mp4"
    p.write_bytes(ftyp)

    boxes = parse_mp4_boxes(str(p))
    f = boxes[0]
    props = f.properties()
    assert props["box_name"] == "FileTypeBox"
    assert props["major_brand"] == major.decode()
    assert props["minor_version"] == minor
    assert props["compatible_brands"] == [b.decode() for b in brands]


def test_largesize_box_mdat(tmp_path):
    # size==1 (largesize): 64-bit size follows; total box size is 16 bytes, no payload.
    header = struct.pack(">I4sQ", 1, b"mdat", 16)
    p = tmp_path / "b.mp4"
    p.write_bytes(header)

    boxes = parse_mp4_boxes(str(p))
    assert boxes[0].type == "mdat"
    assert boxes[0].size == 16
