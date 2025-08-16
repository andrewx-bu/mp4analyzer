import os
import sys
import struct
import pytest

# Temporary: allow `pytest -q` from repo root without packaging the module.
# Prefer packaging parsemp4 and removing this in CI.
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


def test_box_properties():
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

    # Build the avc1 header (78 bytes) followed by avcC box and padding
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
    padding = b"\x00" * 35
    avc1_payload = header + avcc_box + padding
    avc1 = AVCSampleEntry.from_parsed("avc1", 179, 508, avc1_payload, [])
    assert avc1.properties() == {
        "size": 179,
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
