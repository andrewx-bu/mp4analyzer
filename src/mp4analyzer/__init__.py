"""Utilities for MP4 parsing."""

from .boxes import MP4Box
from .parser import parse_mp4_boxes
from .utils import format_box_tree
from .movieinfo import generate_movie_info

try:
    from ._version import version as __version__
except Exception:
    try:
        from setuptools_scm import get_version

        __version__ = get_version(root="..", relative_to=__file__)
    except Exception:
        __version__ = "0.0.0"

__all__ = [
    "MP4Box",
    "parse_mp4_boxes",
    "format_box_tree",
    "generate_movie_info",
]
