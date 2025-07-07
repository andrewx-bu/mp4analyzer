# Video loading and decoding utilities.
import av
from typing import Optional, Tuple
from PyQt6.QtGui import QImage
from models import VideoMetadata, FrameData, VideoFrameCollection


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
    """Decodes video frames from files."""
    
    def __init__(self):
        self._extractor = VideoMetadataExtractor()
    
    def decode_all_frames(self, file_path: str) -> Tuple[Optional[VideoMetadata], VideoFrameCollection]:
        """
        Decode all frames from a video file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Tuple of (metadata, frame_collection). Metadata is None if extraction fails.
            
        Raises:
            VideoLoaderError: If decoding fails
        """
        metadata = self._extractor.extract_metadata(file_path)
        frame_collection = VideoFrameCollection()
        
        if not metadata:
            return None, frame_collection
        
        try:
            self._decode_frames_from_file(file_path, frame_collection)
        except Exception as e:
            raise VideoLoaderError(f"Failed to decode frames from {file_path}: {str(e)}")
        
        return metadata, frame_collection
    
    def _decode_frames_from_file(self, file_path: str, frame_collection: VideoFrameCollection):
        """Decode all frames and add them to the collection."""
        with av.open(file_path) as container:
            video_stream = VideoMetadataExtractor._find_video_stream(container)
            if not video_stream:
                raise VideoLoaderError("No video stream found")
            
            for packet in container.demux(video_stream):
                for frame in packet.decode():
                    qimage = self._convert_frame_to_qimage(frame)
                    frame_metadata = self._extract_frame_metadata(frame, packet)
                    frame_collection.add_frame(qimage, frame_metadata)
    
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
    
    def load_video_file(self, file_path: str) -> Tuple[Optional[VideoMetadata], VideoFrameCollection]:
        """
        Load a video file and decode all frames.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Tuple of (metadata, frame_collection)
        """
        return self._decoder.decode_all_frames(file_path)