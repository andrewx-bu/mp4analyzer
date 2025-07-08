# Video loading and decoding utilities.
import av
from typing import Optional, Tuple, List, Callable
from PyQt6.QtGui import QImage
from models import VideoMetadata, FrameData, LazyVideoFrameCollection


class VideoLoaderError(Exception):
    """Custom exception for video loading errors."""
    pass


class VideoMetadataExtractor:
    """Extracts metadata from video files using PyAV."""
    
    # Maps PyAV pict_type values to readable frame type letters
    FRAME_TYPE_MAP = {
        0: '?',   # Unknown
        1: 'I',   # Intra (keyframe)
        2: 'P',   # Predicted
        3: 'B',   # Bidirectional
        4: 'S',   # Switching
        5: 'SI',  # Switching Intra
        6: 'SP',  # Switching Predicted
        7: 'BI',  # Bidirectional Intra
    }
    
    @staticmethod
    def extract_metadata(file_path: str) -> Optional[VideoMetadata]:
        """
        Extract video metadata from file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            VideoMetadata object if successful, None if failed
        """
        try:
            with av.open(file_path) as container:
                video_stream = VideoMetadataExtractor._find_video_stream(container)
                if not video_stream:
                    return None
                
                # Calculate duration in seconds
                duration_seconds = float(video_stream.duration * video_stream.time_base)
                fps = float(video_stream.base_rate)
                
                return VideoMetadata(
                    file_path=file_path,
                    duration_seconds=duration_seconds,
                    width=video_stream.width,
                    height=video_stream.height,
                    codec_name=video_stream.codec_context.name,
                    total_frames=video_stream.frames,
                    frames_per_second=fps
                )
        except Exception:
            return None
    
    @staticmethod
    def _find_video_stream(container):
        """Find the first video stream in the container."""
        for stream in container.streams:
            if stream.type == 'video':
                return stream
        return None


class VideoFrameDecoder:
    """Utilities for decoding video frames and metadata."""
    
    def __init__(self):
        self._extractor = VideoMetadataExtractor()
    
    def parse_frames(self, file_path: str) -> Tuple[Optional[VideoMetadata], List[FrameData], List[int]]:
        """Parse frame metadata for all frames without decoding to images."""
        metadata = self._extractor.extract_metadata(file_path)

        frame_data: List[FrameData] = []
        frame_pts: List[int] = []

        if not metadata:
            return None, frame_data, frame_pts

        try:
            with av.open(file_path) as container:
                video_stream = VideoMetadataExtractor._find_video_stream(container)
                if not video_stream:
                    raise VideoLoaderError("No video stream found")

                for packet in container.demux(video_stream):
                    for frame in packet.decode():
                        frame_pts.append(int(frame.pts or 0))
                        frame_data.append(self._extract_frame_metadata(frame, packet))
        except Exception as e:
            raise VideoLoaderError(f"Failed to parse frames from {file_path}: {str(e)}")
        
        return metadata, frame_data, frame_pts
    
    def decode_frame_image(self, file_path: str, pts: int) -> Optional[QImage]:
        """Decode a single frame at the given pts."""
        try:
            with av.open(file_path) as container:
                stream = VideoMetadataExtractor._find_video_stream(container)
                if not stream:
                    raise VideoLoaderError("No video stream found")

                container.seek(int(pts), stream=stream, any_frame=False)
                for packet in container.demux(stream):
                    for frame in packet.decode():
                        if frame.pts is None:
                            continue
                        if frame.pts < pts:
                            continue
                        return self._convert_frame_to_qimage(frame)
        except Exception:
            return None

        return None
    
    def _convert_frame_to_qimage(self, av_frame) -> QImage:
        """Convert PyAV frame to QImage."""
        # Convert to RGB24 format for Qt
        rgb_array = av_frame.to_ndarray(format='rgb24')
        
        # Create QImage from the RGB data
        qimage = QImage(
            rgb_array.data,
            av_frame.width,
            av_frame.height,
            QImage.Format.Format_RGB888
        )
        
        # Return a copy to ensure data ownership
        return qimage.copy()
    
    def _extract_frame_metadata(self, av_frame, packet) -> FrameData:
        """Extract metadata from a decoded frame."""
        frame_type = VideoMetadataExtractor.FRAME_TYPE_MAP.get(
            getattr(av_frame, 'pict_type', 0), '?'
        )
        
        packet_size = getattr(packet, 'size', 0)
        
        return FrameData(
            size_bytes=packet_size,
            frame_type=frame_type
        )


class VideoLoader:
    """Main interface for loading video files."""
    
    def __init__(self):
        self._decoder = VideoFrameDecoder()
    
    def load_video_file(self, file_path: str, log_callback: Optional[Callable[[str], None]] = None) -> Tuple[Optional[VideoMetadata], LazyVideoFrameCollection]:
        """Load a video file using lazy frame decoding."""
        metadata, frame_meta, frame_pts = self._decoder.parse_frames(file_path)

        collection = LazyVideoFrameCollection(file_path, frame_pts, frame_meta, log_callback=log_callback)

        return metadata, collection