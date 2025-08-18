"""MP4 box implementations."""

from .base import MP4Box
from .ftyp import FileTypeBox
from .mvhd import MovieHeaderBox
from .tkhd import TrackHeaderBox
from .mdhd import MediaHeaderBox
from .iods import ObjectDescriptorBox
from .moov import MovieBox
from .moof import MovieFragmentBox
from .mfhd import MovieFragmentHeaderBox
from .traf import TrackFragmentBox
from .tfhd import TrackFragmentHeaderBox
from .mvex import MovieExtendsBox
from .mehd import MovieExtendsHeaderBox
from .trex import TrackExtendsBox
from .trak import TrackBox
from .free import FreeSpaceBox
from .mdat import MediaDataBox
from .edts import EditBox
from .elst import EditListBox
from .hdlr import HandlerBox
from .mdia import MediaBox
from .minf import MediaInformationBox
from .meta import MetaBox
from .ilst import IlstBox
from .data import DataBox
from .vmhd import VideoMediaHeaderBox
from .smhd import SoundMediaHeaderBox
from .dinf import DataInformationBox
from .dref import DataReferenceBox
from .udta import UserDataBox
from .tref import TrackReferenceBox, TrackReferenceTypeBox
from .url_ import DataEntryUrlBox
from .stbl import SampleTableBox
from .stsd import SampleDescriptionBox
from .avc1 import AVCSampleEntry
from .hev1 import HEVCSampleEntry
from .av01 import AV1SampleEntry
from .mp4a import MP4AudioSampleEntry
from .ac4 import AC4SampleEntry
from .dac4 import DAC4Box
from .avcc import AVCConfigurationBox
from .hvcc import HEVCConfigurationBox
from .av1c import AV1CodecConfigurationBox
from .btrt import BitRateBox
from .colr import ColourInformationBox
from .pasp import PixelAspectRatioBox
from .fiel import FieldHandlingBox
from .esds import ElementaryStreamDescriptorBox
from .stts import TimeToSampleBox
from .ctts import CompositionOffsetBox
from .stss import SyncSampleBox
from .sdtp import SampleDependencyTypeBox
from .stsc import SampleToChunkBox
from .stsz import SampleSizeBox
from .stco import ChunkOffsetBox
from .sgpd import SampleGroupDescriptionBox
from .sbgp import SampleToGroupBox
from .chpl import ChapterListBox
from .text import TextSampleEntry
from .gmhd import GenericMediaHeaderBox, GenericMediaInfoBox, TextMediaHeaderBox


__all__ = [
    "MP4Box",
    "FileTypeBox",
    "MovieHeaderBox",
    "TrackHeaderBox",
    "MediaHeaderBox",
    "ObjectDescriptorBox",
    "MovieBox",
    "MovieFragmentBox",
    "MovieFragmentHeaderBox",
    "TrackFragmentBox",
    "TrackFragmentHeaderBox",
    "MovieExtendsBox",
    "MovieExtendsHeaderBox",
    "TrackExtendsBox",
    "TrackBox",
    "FreeSpaceBox",
    "MediaDataBox",
    "EditBox",
    "EditListBox",
    "HandlerBox",
    "MediaBox",
    "MediaInformationBox",
    "MetaBox",
    "IlstBox",
    "DataBox",
    "VideoMediaHeaderBox",
    "SoundMediaHeaderBox",
    "DataInformationBox",
    "DataReferenceBox",
    "UserDataBox",
    "TrackReferenceBox",
    "TrackReferenceTypeBox",
    "DataEntryUrlBox",
    "SampleTableBox",
    "SampleDescriptionBox",
    "AVCSampleEntry",
    "HEVCSampleEntry",
    "AV1SampleEntry",
    "MP4AudioSampleEntry",
    "AC4SampleEntry",
    "DAC4Box",
    "AVCConfigurationBox",
    "HEVCConfigurationBox",
    "AV1CodecConfigurationBox",
    "BitRateBox",
    "ColourInformationBox",
    "PixelAspectRatioBox",
    "FieldHandlingBox",
    "ElementaryStreamDescriptorBox",
    "TimeToSampleBox",
    "CompositionOffsetBox",
    "SyncSampleBox",
    "SampleDependencyTypeBox",
    "SampleToChunkBox",
    "SampleSizeBox",
    "ChunkOffsetBox",
    "SampleGroupDescriptionBox",
    "SampleToGroupBox",
    "ChapterListBox",
    "TextSampleEntry",
    "GenericMediaHeaderBox",
    "GenericMediaInfoBox",
    "TextMediaHeaderBox",
]
