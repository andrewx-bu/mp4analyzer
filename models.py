# Data models for MP4 Analyzer application.
import subprocess
import threading
from dataclasses import dataclass
from collections import OrderedDict
from typing import Optional, List, Dict, Callable
from PyQt6.QtGui import QImage
from PIL import Image
import io
import os
import tempfile


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
    timestamp: float  # Frame timestamp in seconds

    @property
    def is_keyframe(self) -> bool:
        """Check if this is a keyframe (I-frame)."""
        return self.frame_type == 'I'


class LazyVideoFrameCollection:
    """Lazily decodes video frames using FFmpeg and caches them."""

    def __init__(self, file_path: str, frame_timestamps: List[float],
        frame_metadata: List[FrameData], cache_size: int = 120,
        log_callback: Optional[Callable[[str], None]] = None):
        self._file_path = file_path
        self._frame_timestamps = frame_timestamps
        self._frame_metadata = frame_metadata

        self._cache: "OrderedDict[int, QImage]" = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()
        self._log_callback = log_callback
        self._temp_dir = tempfile.mkdtemp()
    
    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    # Basic collection helpers
    @property
    def count(self) -> int:
        return len(self._frame_timestamps)

    @property
    def is_empty(self) -> bool:
        return len(self._frame_timestamps) == 0

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
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = tempfile.mkdtemp()
        except Exception:
            pass
    
    def set_log_callback(self, callback: Optional[Callable[[str], None]]):
        """Update the logging callback."""
        self._log_callback = callback

    def _decode_frame_ffmpeg(self, index: int) -> Optional[QImage]:
        """Decode a specific frame using FFmpeg."""
        if not (0 <= index < self.count):
            return None

        timestamp = self._frame_timestamps[index]
        self._log(f"Decoding frame {index} at timestamp {timestamp:.3f}s")
        
        try:
            # Create temporary file for the frame
            temp_frame_path = os.path.join(self._temp_dir, f"frame_{index}.png")
            
            # Use FFmpeg to extract the specific frame
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),  # Seek to timestamp
                '-i', self._file_path,  # Input file
                '-frames:v', '1',       # Extract only one frame
                '-q:v', '2',           # High quality
                '-y',                   # Overwrite output file
                temp_frame_path
            ]
            
            # Run FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                self._log(f"FFmpeg failed for frame {index}: {result.stderr}")
                return None
            
            # Load the extracted frame
            if os.path.exists(temp_frame_path):
                # Load with PIL and convert to QImage
                with Image.open(temp_frame_path) as pil_image:
                    # Convert to RGB if necessary
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    
                    # Convert PIL image to QImage
                    qimage = self._pil_to_qimage(pil_image)
                    
                    # Cache the frame
                    with self._lock:
                        self._cache[index] = qimage
                        while len(self._cache) > self._cache_size:
                            self._cache.popitem(last=False)
                        self._log(f"Cached frame {index}")
                    
                    # Clean up temporary file
                    os.remove(temp_frame_path)
                    
                    return qimage
            else:
                self._log(f"Frame file not created: {temp_frame_path}")
                return None
                
        except Exception as e:
            self._log(f"Exception while decoding frame {index}: {str(e)}")
            return None

    def _pil_to_qimage(self, pil_image: Image.Image) -> QImage:
        """Convert PIL Image to QImage."""
        # Convert PIL image to bytes
        byte_array = io.BytesIO()
        pil_image.save(byte_array, format='PNG')
        byte_data = byte_array.getvalue()
        
        # Create QImage from bytes
        qimage = QImage()
        qimage.loadFromData(byte_data)
        
        return qimage

    def _find_gop_start(self, index: int) -> int:
        """Find the start of the GOP (Group of Pictures) for the given frame."""
        for i in range(index, -1, -1):
            if i < len(self._frame_metadata) and self._frame_metadata[i].is_keyframe:
                return i
        return 0

    def __del__(self):
        """Cleanup temporary directory on destruction."""
        try:
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass