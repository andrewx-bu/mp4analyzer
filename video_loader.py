# Video loading and decoding utilities using FFmpeg/FFprobe.
import subprocess
import json
import os
from typing import Optional, Tuple, List, Callable
from models import VideoMetadata, FrameData, LazyVideoFrameCollection


class VideoLoaderError(Exception):
    pass


def _run_ffmpeg_cmd(cmd: List[str]) -> Optional[str]:
    """Run FFmpeg/FFprobe command and return stdout."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return result.stdout if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def extract_metadata(file_path: str) -> Optional[VideoMetadata]:
    """Extract video metadata from file using FFprobe."""
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-show_format', file_path]
    output = _run_ffmpeg_cmd(cmd)
    
    if not output:
        return None
    
    try:
        data = json.loads(output)
        video_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), None)
        
        if not video_stream:
            return None
        
        duration = float(video_stream.get('duration', 0)) or float(data.get('format', {}).get('duration', 0))
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        codec = video_stream.get('codec_name', 'unknown')
        
        # Calculate FPS
        fps_str = video_stream.get('r_frame_rate', '0/1')
        num, den = map(int, fps_str.split('/'))
        fps = num / den if den != 0 else 0
        
        # Calculate total frames
        total_frames = int(video_stream.get('nb_frames', 0)) or int(duration * fps) if duration and fps else 0
        
        return VideoMetadata(file_path, duration, width, height, codec, total_frames, fps)
    except:
        return None


def parse_frames(file_path: str) -> Tuple[Optional[VideoMetadata], List[FrameData], List[float]]:
    """Parse frame metadata using FFprobe."""
    metadata = extract_metadata(file_path)
    
    if not metadata:
        return None, [], []
    
    cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', 
           '-show_entries', 'frame=pkt_size,pict_type,best_effort_timestamp_time',
           '-print_format', 'json', file_path]
    
    output = _run_ffmpeg_cmd(cmd)
    frame_data, timestamps = [], []
    
    if output:
        try:
            frames = json.loads(output).get('frames', [])
            for frame in frames:
                size = int(frame.get('pkt_size', 0))
                pict_type = frame.get('pict_type', '?')
                timestamp = float(frame.get('best_effort_timestamp_time', 0))
                
                frame_data.append(FrameData(size, pict_type, timestamp))
                timestamps.append(timestamp)
        except:
            pass
    
    # Generate approximate timestamps if none found
    if not timestamps and metadata.total_frames > 0:
        for i in range(metadata.total_frames):
            timestamp = i / metadata.frames_per_second
            timestamps.append(timestamp)
            frame_data.append(FrameData(0, '?', timestamp))
    
    return metadata, frame_data, timestamps


def check_ffmpeg() -> Tuple[bool, bool]:
    """Check if FFmpeg and FFprobe are available."""
    ffmpeg_ok = _run_ffmpeg_cmd(['ffmpeg', '-version']) is not None
    ffprobe_ok = _run_ffmpeg_cmd(['ffprobe', '-version']) is not None
    return ffmpeg_ok, ffprobe_ok


class VideoLoader:
    """Main interface for loading video files using FFmpeg."""
    
    def __init__(self):
        ffmpeg_ok, ffprobe_ok = check_ffmpeg()
        if not ffmpeg_ok:
            raise VideoLoaderError("FFmpeg not available. Install FFmpeg and ensure it's in PATH.")
        if not ffprobe_ok:
            raise VideoLoaderError("FFprobe not available. Install FFmpeg and ensure it's in PATH.")
    
    def load_video_file(self, file_path: str, log_callback: Optional[Callable[[str], None]] = None) -> Tuple[Optional[VideoMetadata], LazyVideoFrameCollection]:
        """Load a video file using lazy frame decoding."""
        if log_callback:
            log_callback("Using FFmpeg for video processing...")
        
        metadata, frame_meta, timestamps = parse_frames(file_path)
        return metadata, LazyVideoFrameCollection(file_path, timestamps, frame_meta, log_callback=log_callback)