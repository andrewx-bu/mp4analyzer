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

        duration = float(video_stream.get('duration', 0) or 0) or float(data.get('format', {}).get('duration', 0) or 0)
        width = int(video_stream.get('width', 0) or 0)
        height = int(video_stream.get('height', 0) or 0)
        codec = video_stream.get('codec_name', 'unknown') or 'unknown'

        # Calculate FPS
        fps_str = video_stream.get('r_frame_rate', '0/1')
        try:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den != 0 else 0.0
        except Exception:
            fps = 0.0

        # Calculate total frames
        total_frames = 0
        try:
            total_frames = int(video_stream.get('nb_frames', 0) or 0)
        except Exception:
            total_frames = int(duration * fps) if duration and fps else 0

        return VideoMetadata(file_path, duration, width, height, codec, total_frames, fps)
    except Exception:
        return None


def parse_frames(file_path: str) -> Tuple[Optional[VideoMetadata], List[FrameData], List[float]]:
    """
    Parse frame metadata with integer PTS (ticks) and decode order (packet order via file position).
    `timestamp` is in seconds and derived from PTS * time_base.
    """
    metadata = extract_metadata(file_path)
    if not metadata:
        return None, [], []

    def _run(cmd):
        return _run_ffmpeg_cmd(cmd) or ""

    # Get the stream time_base to convert ticks -> seconds
    tb_cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=time_base', '-of', 'json', file_path
    ]
    tb_json = {}
    try:
        tb_json = json.loads(_run(tb_cmd)) or {}
    except Exception:
        pass
    tb_str = ((tb_json.get('streams') or [{}])[0]).get('time_base', '1/1')
    try:
        tb_num, tb_den = map(int, tb_str.split('/'))
    except Exception:
        tb_num, tb_den = 1, 1  # fallback

    # Get packets in stream order (decode order) with their file pos
    pkt_cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'packet=pos,flags,size',  # we only need pos to map decode order
        '-of', 'json', file_path
    ]
    pkt_json = {}
    try:
        pkt_json = json.loads(_run(pkt_cmd)) or {}
    except Exception:
        pass
    packets = pkt_json.get('packets', []) or []

    # Map packet file position -> decode index
    pos_to_decode_idx = {}
    for i, p in enumerate(packets):
        pos = p.get('pos')
        if pos is not None and pos != 'N/A':
            try:
                pos_to_decode_idx[int(pos)] = i
            except Exception:
                continue

    # Get frames with integer timestamps and pkt_pos
    frm_cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries',
        'frame=pkt_pos,pict_type,pkt_size,pkt_pts,pkt_dts,best_effort_timestamp',
        '-of', 'json', file_path
    ]
    frames_json = {}
    try:
        frames_json = json.loads(_run(frm_cmd)) or {}
    except Exception:
        pass
    frames = frames_json.get('frames', []) or []

    def to_int(x, default=None):
        if x is None or x == 'N/A':
            return default
        try:
            return int(x)
        except Exception:
            return default

    frame_data: List[FrameData] = []
    timestamps: List[float] = []

    for f in frames:
        size_bytes = int(f.get('pkt_size', 0) or 0)
        frame_type = f.get('pict_type', '?') or '?'

        # Integer PTS ticks: prefer pkt_pts, fall back to best_effort_timestamp
        pts_ticks = to_int(f.get('pkt_pts'))
        if pts_ticks is None:
            pts_ticks = to_int(f.get('best_effort_timestamp'), 0)

        # seconds = pts * (num/den)
        timestamp_sec = (pts_ticks * tb_num / tb_den) if (pts_ticks is not None and tb_den != 0) else 0.0

        # Decode order via packet file offset
        pkt_pos = f.get('pkt_pos')
        if pkt_pos is not None and pkt_pos != 'N/A':
            try:
                decode_order = pos_to_decode_idx.get(int(pkt_pos))
            except Exception:
                decode_order = None
        else:
            decode_order = None

        # Fallback if we couldn't map by pos (rare): append-sequential
        if decode_order is None:
            decode_order = len(frame_data)

        frame_data.append(FrameData(
            size_bytes=size_bytes,
            frame_type=frame_type,
            timestamp=float(timestamp_sec),  # display time (seconds)
            pts=int(pts_ticks or 0),         # integer ticks in stream time_base
            decode_order=int(decode_order),  # true decode order via packet index
        ))
        timestamps.append(float(timestamp_sec))

    # If no timestamps at all, synthesize from FPS
    if not timestamps and metadata and metadata.total_frames > 0 and metadata.frames_per_second > 0:
        for i in range(metadata.total_frames):
            t = i / metadata.frames_per_second
            frame_data.append(FrameData(
                size_bytes=0,
                frame_type='?',
                timestamp=t,
                pts=int(round(t * (tb_den / tb_num))) if tb_num != 0 else 0,  # back-compute ticks from seconds
                decode_order=i
            ))
            timestamps.append(t)

    if frame_data:
        # Sort by decode_order, then by original index for stability
        sorted_indices = sorted(range(len(frame_data)), key=lambda i: (frame_data[i].decode_order, i))
        
        # Update decode_order to be contiguous 0..N-1
        for new_order, orig_idx in enumerate(sorted_indices):
            frame_data[orig_idx].decode_order = new_order

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
