# Data models for MP4 Analyzer application.
from dataclasses import dataclass
from typing import Optional, List
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


class VideoFrameCollection:
    """Container for managing decoded video frames and their metadata."""
    
    def __init__(self):
        self._frames: List[QImage] = []
        self._frame_metadata: List[FrameData] = []
    
    def add_frame(self, image: QImage, metadata: FrameData):
        """Add a decoded frame with its metadata."""
        self._frames.append(image)
        self._frame_metadata.append(metadata)
    
    def clear(self):
        """Clear all frames and metadata."""
        self._frames.clear()
        self._frame_metadata.clear()
    
    @property
    def count(self) -> int:
        """Get total number of frames."""
        return len(self._frames)
    
    @property
    def is_empty(self) -> bool:
        """Check if collection is empty."""
        return len(self._frames) == 0
    
    def get_frame(self, index: int) -> Optional[QImage]:
        """Get frame at specific index."""
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None
    
    def get_frame_metadata(self, index: int) -> Optional[FrameData]:
        """Get frame metadata at specific index."""
        if 0 <= index < len(self._frame_metadata):
            return self._frame_metadata[index]
        return None
    
    @property
    def frame_metadata_list(self) -> List[FrameData]:
        """Get list of all frame metadata."""
        return self._frame_metadata.copy()
    
    def get_valid_index(self, requested_index: int) -> int:
        """Clamp index to valid range."""
        if self.is_empty:
            return 0
        return max(0, min(requested_index, self.count - 1))