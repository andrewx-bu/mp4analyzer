# Data models for MP4 Analyzer application.
import av
import threading
from dataclasses import dataclass
from collections import OrderedDict
from typing import Optional, List, Dict, Callable
from PyQt6.QtGui import QImage


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
        """Get resolution as formatted string."""
        return f"{self.width}x{self.height}"

    @property
    def duration_text(self) -> str:
        """Get duration as formatted string."""
        return f"{self.duration_seconds:.2f}s"


@dataclass
class FrameData:
    """Information about a single video frame."""
    size_bytes: int
    frame_type: str  # 'I', 'P', 'B', etc.

    @property
    def is_keyframe(self) -> bool:
        """Check if this is a keyframe (I-frame)."""
        return self.frame_type == 'I'


class LazyVideoFrameCollection:
    """Lazily decodes video frames and caches them."""

    def __init__(self, file_path: str, frame_pts: List[int],
        frame_metadata: List[FrameData], cache_size: int = 120,
        log_callback: Optional[Callable[[str], None]] = None):
        self._file_path = file_path
        self._frame_pts = frame_pts
        self._frame_metadata = frame_metadata

        self._cache: "OrderedDict[int, QImage]" = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()
        self._log_callback = log_callback
    
    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    # Basic collection helpers
    @property
    def count(self) -> int:
        return len(self._frame_pts)

    @property
    def is_empty(self) -> bool:
        return len(self._frame_pts) == 0

    def get_valid_index(self, requested_index: int) -> int:
        if self.is_empty:
            return 0
        return max(0, min(requested_index, self.count - 1))

    @property
    def frame_metadata_list(self) -> List[FrameData]:
        return self._frame_metadata.copy()

    def get_frame_metadata(self, index: int) -> Optional[FrameData]:
        if 0 <= index < len(self._frame_metadata):
            return self._frame_metadata[index]
        return None

    # Frame retrieval
    def get_frame(self, index: int) -> Optional[QImage]:
        """Retrieve a frame, decoding on demand."""
        with self._lock:
            if index in self._cache:
                img = self._cache.pop(index)
                self._cache[index] = img
                self._log(f"Frame {index} retrieved from cache")
                return img

        img = self._decode_frame(index)
        if img:
            self._log(f"Frame {index} decoded")
        else:
            self._log(f"Failed to decode frame {index}")
        return img

    def clear(self):
        with self._lock:
            self._cache.clear()
    
    def set_log_callback(self, callback: Optional[Callable[[str], None]]):
        """Update the logging callback."""
        self._log_callback = callback

    # Internal helpers
    def _convert_frame_to_qimage(self, av_frame) -> QImage:
        rgb_array = av_frame.to_ndarray(format="rgb24")
        qimage = QImage(
            rgb_array.data,
            av_frame.width,
            av_frame.height,
            QImage.Format.Format_RGB888,
        )
        return qimage.copy()

    def _decode_frame(self, index: int) -> Optional[QImage]:
        if not (0 <= index < self.count):
            return None

        pts = self._frame_pts[index]
        self._log(f"Decoding frame {index} (pts {pts})")
        try:
            with av.open(self._file_path) as container:
                stream = next(s for s in container.streams if s.type == "video")
                container.seek(int(pts), stream=stream, any_frame=False)

                current_index = self._find_gop_start(index)
                self._log(f"Starting decode at GOP frame {current_index}")
                while current_index < index and current_index in self._cache:
                    current_index += 1
                for packet in container.demux(stream):
                    for frame in packet.decode():
                        if frame.pts is None:
                            continue
                        if frame.pts < self._frame_pts[current_index]:
                            continue

                        image = self._convert_frame_to_qimage(frame)
                        with self._lock:
                            self._cache[current_index] = image
                            while len(self._cache) > self._cache_size:
                                self._cache.popitem(last=False)
                            self._log(f"Cached frame {current_index}")

                        if current_index == index:
                            self._log(f"Decoded requested frame {index}")
                            return image

                        current_index += 1
                        if current_index >= self.count:
                            return None
        except Exception:
            self._log("Exception while decoding frame")
            return None

        return None

    def _find_gop_start(self, index: int) -> int:
        for i in range(index, -1, -1):
            if self._frame_metadata[i].is_keyframe:
                return i
        return 0