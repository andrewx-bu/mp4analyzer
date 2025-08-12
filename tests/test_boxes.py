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
        "data": b"",
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
