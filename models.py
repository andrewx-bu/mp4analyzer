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

    @property
    def is_keyframe(self) -> bool:
        return self.frame_type == 'I'


class LazyVideoFrameCollection:
    """Lazily decodes video frames using FFmpeg and caches them."""

    def __init__(self, file_path: str, frame_timestamps: List[float],
                 frame_metadata: List[FrameData], cache_size: int = 120,
                 log_callback: Optional[Callable[[str], None]] = None):
        self._file_path = file_path
        self._frame_timestamps = frame_timestamps
        self._frame_metadata = frame_metadata
        self._cache: OrderedDict[int, QImage] = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()
        self._log_callback = log_callback
        self._temp_dir = tempfile.mkdtemp()

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
        return self._frame_metadata[index] if 0 <= index < len(self._frame_metadata) else None

    def get_frame(self, index: int) -> Optional[QImage]:
        """Retrieve a frame, decoding on demand using FFmpeg."""
        with self._lock:
            if index in self._cache:
                img = self._cache.pop(index)
                self._cache[index] = img
                self._log(f"Frame {index} retrieved from cache")
                return img

        img = self._decode_frame_ffmpeg(index)
        if img:
            self._log(f"Frame {index} decoded with FFmpeg")
        else:
            self._log(f"Failed to decode frame {index}")
        return img

    def clear(self):
        with self._lock:
            self._cache.clear()
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = tempfile.mkdtemp()
        except:
            pass

    def set_log_callback(self, callback: Optional[Callable[[str], None]]):
        self._log_callback = callback

    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    def _decode_frame_ffmpeg(self, index: int) -> Optional[QImage]:
        """Decode a specific frame using FFmpeg."""
        if not (0 <= index < self.count):
            return None

        timestamp = self._frame_timestamps[index]
        self._log(f"Decoding frame {index} at timestamp {timestamp:.3f}s")
        
        temp_frame_path = os.path.join(self._temp_dir, f"frame_{index}.png")
        
        try:
            cmd = ['ffmpeg', '-ss', str(timestamp), '-i', self._file_path, 
                   '-frames:v', '1', '-q:v', '2', '-y', temp_frame_path]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0 or not os.path.exists(temp_frame_path):
                self._log(f"FFmpeg failed for frame {index}")
                return None
            
            with Image.open(temp_frame_path) as pil_image:
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Convert PIL to QImage
                byte_array = io.BytesIO()
                pil_image.save(byte_array, format='PNG')
                qimage = QImage()
                qimage.loadFromData(byte_array.getvalue())
                
                # Cache the frame
                with self._lock:
                    self._cache[index] = qimage
                    while len(self._cache) > self._cache_size:
                        self._cache.popitem(last=False)
                    self._log(f"Cached frame {index}")
                
                os.remove(temp_frame_path)
                return qimage
                
        except Exception as e:
            self._log(f"Exception while decoding frame {index}: {str(e)}")
            return None

    def __del__(self):
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except:
            pass