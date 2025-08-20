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
        """Formatted resolution, e.g., '1920x1080'."""
        return f"{self.width}x{self.height}"

    @property
    def duration_text(self) -> str:
        """Formatted duration in seconds, e.g., '12.34s'."""
        return f"{self.duration_seconds:.2f}s"


@dataclass
class FrameData:
    """Information about a single video frame."""

    size_bytes: int
    frame_type: str  # I / P / B / ? frame type
    timestamp: float  # display timestamp in seconds
    pts: int  # presentation timestamp (ticks)
    decode_order: int  # order in which frame is decoded
    ref_prev: Optional[int] = None  # index of past reference frame
    ref_next: Optional[int] = None  # index of future reference frame

    @property
    def is_keyframe(self) -> bool:
        """True if this frame is an I-frame (keyframe)."""
        return self.frame_type == "I"


class LazyVideoFrameCollection:
    """Lazily decodes video frames using FFmpeg and caches them for reuse."""

    def __init__(
        self,
        file_path: str,
        timestamps: List[float],
        frame_metadata: List[FrameData],
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self._file_path = file_path
        self._timestamps = timestamps
        self._frame_metadata = frame_metadata
        self._log_callback = log_callback
        self._cache: OrderedDict[int, QImage] = OrderedDict()
        self._compressed_cache: OrderedDict[int, bytes] = OrderedDict()
        self._lock = threading.Lock()
        self._last_cache_log_index: Optional[int] = None

        # Dynamic cache sizing based on available memory
        cache_size = self._calculate_optimal_cache_size()
        self._cache_size = cache_size
        self._cache_quality = 75  # JPEG quality for caching (faster compression)
        self._temp_dir = tempfile.mkdtemp()  # directory for decoded temp frames

    def _calculate_optimal_cache_size(self) -> int:
        """Calculate optimal cache size based on available memory."""
        try:
            import psutil

            # Get available memory in MB
            available_mb = psutil.virtual_memory().available // (1024 * 1024)

            # Find frame size (fallback to 1080p)
            width = getattr(self, "_width", 1920) or 1920
            height = getattr(self, "_height", 1080) or 1080
            estimated_frame_mb = max(1, (4 * width * height) // (1024 * 1024))

            # Use at most ~25% of available RAM with guardrails
            max_cache_mb = max(64, int(available_mb * 0.25))
            optimal_cache_size = int(max_cache_mb // estimated_frame_mb)
            optimal_cache_size = max(10, min(120, optimal_cache_size))

            self._log(
                f"Dynamic cache sizing: {optimal_cache_size} frames ({max_cache_mb:.1f}MB limit)"
            )
            return optimal_cache_size

        except Exception:
            # Fallback if psutil not available
            return 30

    @property
    def count(self) -> int:
        """Total number of frames."""
        return len(self._timestamps)

    @property
    def is_empty(self) -> bool:
        """True if no frames are available."""
        return len(self._timestamps) == 0

    def get_valid_index(self, requested_index: int) -> int:
        """Clamp requested frame index into valid range."""
        return max(0, min(requested_index, self.count - 1)) if not self.is_empty else 0

    @property
    def frame_metadata_list(self) -> List[FrameData]:
        """Return a copy of all frame metadata."""
        return self._frame_metadata.copy()

    def get_frame_metadata(self, index: int) -> Optional[FrameData]:
        """Get metadata for a specific frame index."""
        return (
            self._frame_metadata[index]
            if 0 <= index < len(self._frame_metadata)
            else None
        )

    def get_frame(self, index: int) -> Optional[QImage]:
        """Retrieve a frame, decoding its GOP if needed. Uses cache when possible."""
        # Try uncompressed cache first
        with self._lock:
            if index in self._cache:
                # Move to end of LRU cache
                img = self._cache.pop(index)
                self._cache[index] = img
                if self._last_cache_log_index != index:
                    self._log(f"cache: hit raw idx={index}")
                    self._last_cache_log_index = index
                return img

        # Try compressed cache
        compressed_frame = self._load_from_compressed_cache(index)
        if compressed_frame:
            if self._last_cache_log_index != index:
                self._log(f"cache: hit jpeg idx={index}")
                self._last_cache_log_index = index
            return compressed_frame

        # Decode GOP containing this frame if not cached
        if self._last_cache_log_index != index:
            self._log(f"cache: miss idx={index}")
            self._last_cache_log_index = index
        self._decode_gop_frames(index)

        # Try again after decoding
        with self._lock:
            if index in self._cache:
                img = self._cache.pop(index)
                self._cache[index] = img
                return img

        self._log(f"Failed to decode frame {index}")
        return None

    def _cache_compressed_frame(self, index: int, qimage: QImage):
        """Cache frame as compressed JPEG data to save memory."""
        from PyQt6.QtCore import QBuffer

        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        qimage.save(buffer, "JPEG", self._cache_quality)

        with self._lock:
            # Store python-owned bytes and move to end for LRU
            data = bytes(buffer.data())
            self._compressed_cache[index] = data
            self._compressed_cache.move_to_end(index)
            self._log(
                f"cache: insert jpeg idx={index} sizes raw={len(self._cache)} jpeg={len(self._compressed_cache)}"
            )
            # Enforce a single combined budget across raw+compressed caches
            while (len(self._compressed_cache) + len(self._cache)) > self._cache_size:
                # Prefer evicting raw frames first
                if self._cache:
                    ev_idx, _ = self._cache.popitem(last=False)
                    self._log(
                        f"cache: evict raw idx={ev_idx} sizes raw={len(self._cache)} jpeg={len(self._compressed_cache)}"
                    )
                else:
                    ev_idx, _ = self._compressed_cache.popitem(last=False)
                    self._log(
                        f"cache: evict jpeg idx={ev_idx} sizes raw={len(self._cache)} jpeg={len(self._compressed_cache)}"
                    )

    def _load_from_compressed_cache(self, index: int) -> Optional[QImage]:
        """Load frame from compressed cache."""
        with self._lock:
            if index in self._compressed_cache:
                compressed_data = self._compressed_cache.pop(index)
                self._compressed_cache[index] = compressed_data  # Move to end

                qimage = QImage()
                qimage.loadFromData(compressed_data, "JPEG")
                return qimage
        return None

    def clear(self):
        """Clear cache and reset temp directory."""
        with self._lock:
            self._cache.clear()
            self._compressed_cache.clear()
        self._log("cache: clear")
        self._last_cache_log_index = None
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = tempfile.mkdtemp()
        except Exception:
            pass

    def set_log_callback(self, callback: Optional[Callable[[str], None]]):
        """Set logging callback function."""
        self._log_callback = callback

    def _log(self, message: str):
        """Send log messages if callback is set."""
        if self._log_callback:
            self._log_callback(message)

    def _decode_single_frame_optimized(self, target_index: int) -> Optional[QImage]:
        """Decode only the target frame using precise seeking."""
        if not (0 <= target_index < self.count):
            return None

        timestamp = self._timestamps[target_index]

        # Optimized FFmpeg command with faster seeking and decoding
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-loglevel",
            "error",
            "-ss",
            str(timestamp),  # Seek before input for faster seeking
            "-i",
            self._file_path,
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-pix_fmt",
            "rgb24",
            "-vcodec",
            "rawvideo",
            "-threads",
            "1",  # Single thread for single frame
            "-avoid_negative_ts",
            "disabled",  # Avoid timestamp adjustments
            "-fflags",
            "+genpts+discardcorrupt",  # Generate PTS, discard corrupt
            "-",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            if result.returncode == 0 and result.stdout:
                # Get frame dimensions from first frame or estimate
                width, height = self._get_frame_dimensions()
                expected_size = width * height * 3  # RGB24

                if len(result.stdout) >= expected_size:
                    # Create QImage directly from raw RGB data
                    qimage = QImage(
                        result.stdout[:expected_size],
                        width,
                        height,
                        QImage.Format.Format_RGB888,
                    )
                    self._log(
                        f"decode: single ok idx={target_index} ts={timestamp:.3f}s"
                    )
                    return qimage.copy()  # Ensure data ownership

        except Exception as e:
            self._log(f"Error decoding frame {target_index}: {e}")

        return None

    def _get_frame_dimensions(self) -> tuple[int, int]:
        """Get frame dimensions, defaulting to 1920x1080 if unknown."""
        # Prefer known metadata if the collection was constructed with it
        w = getattr(self, "_width", None)
        h = getattr(self, "_height", None)
        if isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0:
            return w, h
        # Try to get from cached frame first
        with self._lock:
            for qimage in self._cache.values():
                if qimage and not qimage.isNull():
                    return qimage.width(), qimage.height()

        # Default to common resolution
        return 1920, 1080

    def _decode_gop_frames(self, target_index: int):
        """Decode all frames in the GOP containing target_index, with fallback for large GOPs."""
        if not (0 <= target_index < self.count):
            return

        # Try single-frame decoding first for better performance
        single_frame = self._decode_single_frame_optimized(target_index)
        if single_frame:
            # Cache both uncompressed (for immediate use) and compressed (for memory efficiency)
            with self._lock:
                self._cache[target_index] = single_frame
                while (
                    len(self._cache) > self._cache_size // 2
                ):  # Keep fewer uncompressed frames
                    self._cache.popitem(last=False)

            # Also store compressed version for long-term caching
            self._cache_compressed_frame(target_index, single_frame)
            self._log(f"Single frame decode successful for frame {target_index}")
            return

        # Fallback to GOP decoding if single-frame fails
        # Find GOP boundaries
        gop_start = self._find_gop_start(target_index)
        gop_end = self._find_gop_end(gop_start)
        gop_size = gop_end - gop_start + 1

        # Fallback: decode fewer frames if GOP is too large
        max_decode_frames = 20
        if gop_size > max_decode_frames:
            half_range = max_decode_frames // 2
            decode_start = max(gop_start, target_index - half_range)
            decode_end = min(gop_end, target_index + half_range)
            self._log(
                f"decode: range clip gop={gop_size} [{decode_start}-{decode_end}]"
            )
        else:
            decode_start, decode_end = gop_start, gop_end
            self._log(f"decode: range gop={gop_size} [{decode_start}-{decode_end}]")

        # Skip decoding if most frames are already cached
        with self._lock:
            cached_count = sum(
                1 for i in range(decode_start, decode_end + 1) if i in self._cache
            )
            if cached_count > (decode_end - decode_start + 1) * 0.8:
                self._log(f"Most frames {decode_start}-{decode_end} already cached")
                return

        # Decode required range
        self._decode_frame_range(decode_start, decode_end)

    def _find_gop_start(self, index: int) -> int:
        """Find index of GOP start (nearest previous keyframe)."""
        for i in range(index, -1, -1):
            if i < len(self._frame_metadata) and self._frame_metadata[i].is_keyframe:
                return i
        return 0

    def _find_gop_end(self, gop_start: int) -> int:
        """Find index of GOP end (before next keyframe)."""
        for i in range(gop_start + 1, len(self._frame_metadata)):
            if self._frame_metadata[i].is_keyframe:
                return i - 1
        return len(self._frame_metadata) - 1

    def _decode_frame_range(self, start_index: int, end_index: int):
        """Decode a range of frames using FFmpeg into temporary files, then cache them."""
        if start_index > end_index or start_index < 0 or end_index >= self.count:
            return

        # Duration covers frame span + small buffer
        start_timestamp = self._timestamps[start_index]
        end_timestamp = self._timestamps[end_index]
        duration = end_timestamp - start_timestamp + (1.0 / 30.0)

        temp_pattern = os.path.join(self._temp_dir, "frame_%04d.png")

        try:
            # FFmpeg command to dump frame images
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

            # Load, convert, and cache frames
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

                            # Convert PIL → QImage
                            byte_array = io.BytesIO()
                            pil_image.save(byte_array, format="PNG")
                            qimage = QImage()
                            qimage.loadFromData(byte_array.getvalue())

                            # Cache frame with LRU eviction
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
                    f"cache: insert raw [{min(cached_frames)}-{max(cached_frames)}] count={len(cached_frames)} sizes raw={len(self._cache)} jpeg={len(self._compressed_cache)}"
                )

        except Exception as e:
            self._log(f"Exception decoding range {start_index}-{end_index}: {str(e)}")

    def _decode_frame_ffmpeg(self, index: int) -> Optional[QImage]:
        """Decode a single frame with FFmpeg (slow fallback)."""
        if not (0 <= index < self.count):
            return None

        timestamp = self._timestamps[index]
        temp_frame_path = os.path.join(self._temp_dir, f"frame_single_{index}.png")

        try:
            # Extract single frame
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-loglevel",
                "error",
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

                # Convert PIL → QImage
                byte_array = io.BytesIO()
                pil_image.save(byte_array, format="PNG")
                qimage = QImage()
                qimage.loadFromData(byte_array.getvalue())

                # Cache the frame
                with self._lock:
                    self._cache[index] = qimage
                    while len(self._cache) > self._cache_size:
                        ev_idx, _ = self._cache.popitem(last=False)
                        self._log(
                            f"cache: evict raw idx={ev_idx} sizes raw={len(self._cache)} jpeg={len(self._compressed_cache)}"
                        )
                    self._log(
                        f"cache: insert raw idx={index} sizes raw={len(self._cache)} jpeg={len(self._compressed_cache)}"
                    )

                os.remove(temp_frame_path)
                return qimage

        except Exception as e:
            self._log(f"Exception decoding single frame {index}: {str(e)}")
            return None

    def __del__(self):
        """Cleanup temp directory on deletion."""
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass
