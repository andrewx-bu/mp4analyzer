# Video loading and decoding utilities using FFmpeg/FFprobe.
import subprocess
import json
import os
from typing import Optional, Tuple, List, Callable
from PyQt6.QtGui import QImage
from PIL import Image
import io
from models import VideoMetadata, FrameData, LazyVideoFrameCollection


class VideoLoaderError(Exception):
    """Custom exception for video loading errors."""
    pass


class VideoMetadataExtractor:
    """Extracts metadata from video files using FFprobe."""
    
    @staticmethod
    def extract_metadata(file_path: str) -> Optional[VideoMetadata]:
        """
        Extract video metadata from file using FFprobe.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            VideoMetadata object if successful, None if failed
        """
        try:
            # Use FFprobe to get video metadata
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-show_format',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return None
            
            # Extract metadata
            duration_seconds = float(video_stream.get('duration', 0))
            if duration_seconds == 0:
                # Try to get duration from format
                duration_seconds = float(data.get('format', {}).get('duration', 0))
            
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            codec_name = video_stream.get('codec_name', 'unknown')
            
            # Calculate FPS
            fps_str = video_stream.get('r_frame_rate', '0/1')
            try:
                num, den = map(int, fps_str.split('/'))
                fps = num / den if den != 0 else 0
            except:
                fps = 0
            
            # Calculate total frames
            total_frames = int(video_stream.get('nb_frames', 0))
            if total_frames == 0 and duration_seconds > 0 and fps > 0:
                total_frames = int(duration_seconds * fps)
            
            return VideoMetadata(
                file_path=file_path,
                duration_seconds=duration_seconds,
                width=width,
                height=height,
                codec_name=codec_name,
                total_frames=total_frames,
                frames_per_second=fps
            )
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return None


class VideoFrameDecoder:
    """Utilities for decoding video frames using FFmpeg."""
    
    def __init__(self):
        self._extractor = VideoMetadataExtractor()
    
    def parse_frames(self, file_path: str) -> Tuple[Optional[VideoMetadata], List[FrameData], List[float]]:
        """Parse frame metadata using FFprobe."""
        metadata = self._extractor.extract_metadata(file_path)
        
        frame_data: List[FrameData] = []
        frame_timestamps: List[float] = []
        
        if not metadata:
            return None, frame_data, frame_timestamps
        
        try:
            # Get detailed frame information using FFprobe
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-select_streams', 'v:0',
                '-show_entries', 'frame=pkt_size,pict_type,best_effort_timestamp_time',
                '-print_format', 'json',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                raise VideoLoaderError(f"FFprobe failed: {result.stderr}")
            
            data = json.loads(result.stdout)
            frames = data.get('frames', [])
            
            for frame_info in frames:
                # Extract frame information
                pkt_size = int(frame_info.get('pkt_size', 0))
                pict_type = frame_info.get('pict_type', '?')
                timestamp = float(frame_info.get('best_effort_timestamp_time', 0))
                
                frame_data.append(FrameData(
                    size_bytes=pkt_size,
                    frame_type=pict_type,
                    timestamp=timestamp
                ))
                frame_timestamps.append(timestamp)
            
            # If no frames found, generate approximate timestamps
            if not frame_timestamps and metadata.total_frames > 0:
                for i in range(metadata.total_frames):
                    timestamp = i / metadata.frames_per_second
                    frame_timestamps.append(timestamp)
                    frame_data.append(FrameData(
                        size_bytes=0,
                        frame_type='?',
                        timestamp=timestamp
                    ))
            
        except Exception as e:
            raise VideoLoaderError(f"Failed to parse frames from {file_path}: {str(e)}")
        
        return metadata, frame_data, frame_timestamps
    
    def decode_frame_image(self, file_path: str, timestamp: float) -> Optional[QImage]:
        """Decode a single frame at the given timestamp using FFmpeg."""
        try:
            # Create temporary file for the frame
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_file.close()
            
            # Use FFmpeg to extract the frame
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', file_path,
                '-frames:v', '1',
                '-q:v', '2',
                '-y',
                temp_file.name
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                return None
            
            # Load the extracted frame
            if os.path.exists(temp_file.name):
                with Image.open(temp_file.name) as pil_image:
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    qimage = self._pil_to_qimage(pil_image)
                
                # Clean up
                os.unlink(temp_file.name)
                return qimage
            
        except Exception as e:
            print(f"Error decoding frame: {e}")
            
        return None
    
    def _pil_to_qimage(self, pil_image: Image.Image) -> QImage:
        """Convert PIL Image to QImage."""
        byte_array = io.BytesIO()
        pil_image.save(byte_array, format='PNG')
        byte_data = byte_array.getvalue()
        
        qimage = QImage()
        qimage.loadFromData(byte_data)
        
        return qimage


class FFmpegChecker:
    """Utility to check if FFmpeg and FFprobe are available."""
    
    @staticmethod
    def check_ffmpeg_availability() -> Tuple[bool, bool]:
        """
        Check if FFmpeg and FFprobe are available.
        
        Returns:
            Tuple of (ffmpeg_available, ffprobe_available)
        """
        ffmpeg_available = False
        ffprobe_available = False
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            ffmpeg_available = result.returncode == 0
        except FileNotFoundError:
            pass
        
        try:
            result = subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            ffprobe_available = result.returncode == 0
        except FileNotFoundError:
            pass
        
        return ffmpeg_available, ffprobe_available


class VideoLoader:
    """Main interface for loading video files using FFmpeg."""
    
    def __init__(self):
        self._decoder = VideoFrameDecoder()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        ffmpeg_available, ffprobe_available = FFmpegChecker.check_ffmpeg_availability()
        
        if not ffmpeg_available:
            raise VideoLoaderError("FFmpeg is not available. Please install FFmpeg and ensure it's in your PATH.")
        
        if not ffprobe_available:
            raise VideoLoaderError("FFprobe is not available. Please install FFmpeg (which includes FFprobe) and ensure it's in your PATH.")
    
    def load_video_file(self, file_path: str, log_callback: Optional[Callable[[str], None]] = None) -> Tuple[Optional[VideoMetadata], LazyVideoFrameCollection]:
        """Load a video file using lazy frame decoding with FFmpeg."""
        if log_callback:
            log_callback("Using FFmpeg for video processing...")
        
        metadata, frame_meta, frame_timestamps = self._decoder.parse_frames(file_path)
        
        collection = LazyVideoFrameCollection(
            file_path, 
            frame_timestamps, 
            frame_meta, 
            log_callback=log_callback
        )
        
        return metadata, collection