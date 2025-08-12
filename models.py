# Data models for MP4 Analyzer application.
import subprocess
import threading
import tempfile
import shutil
from dataclasses import dataclass
from collections import OrderedDict
from typing import Optional, List, Callable
from PyQt6.QtGui import QImage
from PIL import Image
import io
import os


@dataclass
class VideoMetadata:
    """Metadata information extracted from a video file."""

    file_path: str
    duration_seconds: float
    width: int
    height: int
    codec_name: str
    total_frames: int
    frames_per_second: float

    @property
    def resolution_text(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def duration_text(self) -> str:
        return f"{self.duration_seconds:.2f}s"


@dataclass
class FrameData:
    """Information about a single video frame."""

    size_bytes: int
    frame_type: str
    timestamp: float
    pts: int
    decode_order: int
    ref_prev: Optional[int] = None  # index of past reference frame
    ref_next: Optional[int] = None  # index of future reference frame

    @property
    def is_keyframe(self) -> bool:
        return self.frame_type == "I"


class LazyVideoFrameCollection:
    """Lazily decodes video frames using FFmpeg and caches them."""

    def __init__(
        self,
        file_path: str,
        frame_timestamps: List[float],
        frame_metadata: List[FrameData],
        cache_size: int = 60,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self._file_path = file_path
        self._frame_timestamps = frame_timestamps
        self._frame_metadata = frame_metadata
        self._cache: OrderedDict[int, QImage] = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()
        self._log_callback = log_callback
        self._temp_dir = tempfile.mkdtemp()
        self._last_cache_log_index = None

    @property
    def count(self) -> int:
        return len(self._frame_timestamps)

    @property
    def is_empty(self) -> bool:
        return len(self._frame_timestamps) == 0

    def get_valid_index(self, requested_index: int) -> int:
        return max(0, min(requested_index, self.count - 1)) if not self.is_empty else 0

    @property
    def frame_metadata_list(self) -> List[FrameData]:
        return self._frame_metadata.copy()

    def get_frame_metadata(self, index: int) -> Optional[FrameData]:
        return (
            self._frame_metadata[index]
            if 0 <= index < len(self._frame_metadata)
            else None
        )

    def get_frame(self, index: int) -> Optional[QImage]:
        """Retrieve a frame, decoding GOP-based on demand using FFmpeg."""
        with self._lock:
            if index in self._cache:
                img = self._cache.pop(index)
                self._cache[index] = img
                if self._last_cache_log_index != index:
                    self._log(f"Frame {index} retrieved from cache")
                    self._last_cache_log_index = index
                return img

        # Decode GOP containing this frame
        self._decode_gop_frames(index)

        # Try to get frame from cache after GOP decode
        with self._lock:
            if index in self._cache:
                img = self._cache.pop(index)
                self._cache[index] = img
                return img

        self._log(f"Failed to decode frame {index}")
        return None

    def clear(self):
        with self._lock:
            self._cache.clear()
        self._last_cache_log_index = None
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = tempfile.mkdtemp()
        except Exception:
            pass

    def set_log_callback(self, callback: Optional[Callable[[str], None]]):
        self._log_callback = callback

    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    def _decode_gop_frames(self, target_index: int):
        """Decode all frames in the GOP containing target_index, with fallback for large GOPs."""
        if not (0 <= target_index < self.count):
            return

        # Find GOP boundaries
        gop_start = self._find_gop_start(target_index)
        gop_end = self._find_gop_end(gop_start)
        gop_size = gop_end - gop_start + 1

        # Fallback for large GOPs - limit to adjacent frames
        max_decode_frames = 20
        if gop_size > max_decode_frames:
            # Decode adjacent frames around target
            half_range = max_decode_frames // 2
            decode_start = max(gop_start, target_index - half_range)
            decode_end = min(gop_end, target_index + half_range)
            self._log(
                f"Large GOP ({gop_size} frames), decoding adjacent frames {decode_start}-{decode_end}"
            )
        else:
            decode_start = gop_start
            decode_end = gop_end
            self._log(
                f"Decoding GOP frames {decode_start}-{decode_end} ({gop_size} frames)"
            )

        # Check if we already have most frames cached
        with self._lock:
            cached_count = sum(
                1 for i in range(decode_start, decode_end + 1) if i in self._cache
            )
            if (
                cached_count > (decode_end - decode_start + 1) * 0.8
            ):  # 80% already cached
                self._log(f"Most frames {decode_start}-{decode_end} already cached")
                return

        # Decode the range
        self._decode_frame_range(decode_start, decode_end)

    def _find_gop_start(self, index: int) -> int:
        """Find the start of the GOP (Group of Pictures) for the given frame."""
        for i in range(index, -1, -1):
            if i < len(self._frame_metadata) and self._frame_metadata[i].is_keyframe:
                return i
        return 0

    def _find_gop_end(self, gop_start: int) -> int:
        """Find the end of the GOP starting at gop_start."""
        for i in range(gop_start + 1, len(self._frame_metadata)):
            if self._frame_metadata[i].is_keyframe:
                return i - 1
        return len(self._frame_metadata) - 1

    def _decode_frame_range(self, start_index: int, end_index: int):
        """Decode a range of frames using FFmpeg."""
        if start_index > end_index or start_index < 0 or end_index >= self.count:
            return

        start_timestamp = self._frame_timestamps[start_index]
        end_timestamp = self._frame_timestamps[end_index]
        duration = end_timestamp - start_timestamp + (1.0 / 30.0)  # Add small buffer

        temp_pattern = os.path.join(self._temp_dir, "frame_%04d.png")

        try:
            cmd = [
                "ffmpeg",
                "-ss",
                str(start_timestamp),
                "-i",
                self._file_path,
                "-t",
                str(duration),
                "-q:v",
                "2",
                "-y",
                temp_pattern,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            if result.returncode != 0:
                self._log(f"FFmpeg failed for range {start_index}-{end_index}")
                return

            # Load and cache decoded frames
            cached_frames = []
            for i in range(start_index, end_index + 1):
                frame_file = os.path.join(
                    self._temp_dir, f"frame_{i - start_index + 1:04d}.png"
                )
                if os.path.exists(frame_file):
                    try:
                        with Image.open(frame_file) as pil_image:
                            if pil_image.mode != "RGB":
                                pil_image = pil_image.convert("RGB")

                            # Convert PIL to QImage
                            byte_array = io.BytesIO()
                            pil_image.save(byte_array, format="PNG")
                            qimage = QImage()
                            qimage.loadFromData(byte_array.getvalue())

                            # Cache the frame
                            with self._lock:
                                self._cache[i] = qimage
                                while len(self._cache) > self._cache_size:
                                    self._cache.popitem(last=False)

                            cached_frames.append(i)

                        os.remove(frame_file)
                    except Exception as e:
                        self._log(f"Error loading frame {i}: {str(e)}")

            if cached_frames:
                self._log(
                    f"Cached frames {min(cached_frames)}-{max(cached_frames)} ({len(cached_frames)} frames)"
                )

        except Exception as e:
            self._log(f"Exception decoding range {start_index}-{end_index}: {str(e)}")

    def _decode_frame_ffmpeg(self, index: int) -> Optional[QImage]:
        """Decode a single frame using FFmpeg (fallback method)."""
        if not (0 <= index < self.count):
            return None

        timestamp = self._frame_timestamps[index]
        temp_frame_path = os.path.join(self._temp_dir, f"frame_single_{index}.png")

        try:
            cmd = [
                "ffmpeg",
                "-ss",
                str(timestamp),
                "-i",
                self._file_path,
                "-frames:v",
                "1",
                "-q:v",
                "2",
                "-y",
                temp_frame_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            if result.returncode != 0 or not os.path.exists(temp_frame_path):
                return None

            with Image.open(temp_frame_path) as pil_image:
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")

                # Convert PIL to QImage
                byte_array = io.BytesIO()
                pil_image.save(byte_array, format="PNG")
                qimage = QImage()
                qimage.loadFromData(byte_array.getvalue())

                # Cache the frame
                with self._lock:
                    self._cache[index] = qimage
                    while len(self._cache) > self._cache_size:
                        self._cache.popitem(last=False)

                os.remove(temp_frame_path)
                return qimage

        except Exception as e:
            self._log(f"Exception decoding single frame {index}: {str(e)}")
            return None

    def __del__(self):
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass
