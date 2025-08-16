# Video loading and decoding utilities using FFmpeg/FFprobe.
import subprocess
import json
import os
from typing import Optional, Tuple, List, Callable
from models import VideoMetadata, FrameData, LazyVideoFrameCollection


class VideoLoaderError(Exception):
    """Custom error for FFmpeg/FFprobe issues."""

    pass


def _run_ffmpeg_cmd(cmd: List[str]) -> Optional[str]:
    """Run an FFmpeg/FFprobe command, return stdout or None on error."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return result.stdout if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def extract_metadata(file_path: str) -> Optional[VideoMetadata]:
    """Extract basic video metadata (duration, size, codec, fps, total frames)."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        file_path,
    ]
    output = _run_ffmpeg_cmd(cmd)
    if not output:
        return None

    try:
        data = json.loads(output)
        # Pick first video stream
        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"), None
        )
        if not video_stream:
            return None

        # Duration fallback: try stream, else format
        duration = float(video_stream.get("duration", 0) or 0) or float(
            data.get("format", {}).get("duration", 0) or 0
        )
        width = int(video_stream.get("width", 0) or 0)
        height = int(video_stream.get("height", 0) or 0)
        codec = video_stream.get("codec_name", "unknown") or "unknown"

        # FPS = r_frame_rate numerator/denominator
        fps_str = video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = map(int, fps_str.split("/"))
            fps = num / den if den != 0 else 0.0
        except Exception:
            fps = 0.0

        # Total frames (prefer nb_frames, else duration * fps)
        try:
            total_frames = int(video_stream.get("nb_frames", 0) or 0)
        except Exception:
            total_frames = int(duration * fps) if duration and fps else 0

        return VideoMetadata(
            file_path, duration, width, height, codec, total_frames, fps
        )
    except Exception:
        return None


def parse_frames(
    file_path: str,
) -> Tuple[Optional[VideoMetadata], List[FrameData], List[float]]:
    """
    Parse per-frame metadata:
      - pts (ticks), decode order (packet order), timestamp (sec).
      - motion vector info to detect forward/backward references.
    """
    metadata = extract_metadata(file_path)
    if not metadata:
        return None, [], []

    def _run(cmd):
        return _run_ffmpeg_cmd(cmd) or ""

    # --- Stream time base (to convert ticks → seconds) ---
    tb_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=time_base",
        "-of",
        "json",
        file_path,
    ]
    tb_json = {}
    try:
        tb_json = json.loads(_run(tb_cmd)) or {}
    except Exception:
        pass
    tb_str = ((tb_json.get("streams") or [{}])[0]).get("time_base", "1/1")
    try:
        tb_num, tb_den = map(int, tb_str.split("/"))
    except Exception:
        tb_num, tb_den = 1, 1

    # --- Packets (file pos → decode order index) ---
    pkt_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "packet=pos,flags,size",
        "-of",
        "json",
        file_path,
    ]
    pkt_json = {}
    try:
        pkt_json = json.loads(_run(pkt_cmd)) or {}
    except Exception:
        pass
    packets = pkt_json.get("packets", []) or []

    pos_to_decode_idx = {}
    for i, p in enumerate(packets):
        pos = p.get("pos")
        if pos not in (None, "N/A"):
            try:
                pos_to_decode_idx[int(pos)] = i
            except Exception:
                continue

    # --- Frame-level data (pts, type, size, mv side-data) ---
    frm_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-export_side_data",
        "+mvs",
        "-show_entries",
        "frame=pkt_pos,pict_type,pkt_size,pkt_pts,pkt_dts,"
        "best_effort_timestamp,side_data_list",
        "-of",
        "json",
        file_path,
    ]
    frames_json = {}
    try:
        frames_json = json.loads(_run(frm_cmd)) or {}
    except Exception:
        pass
    frames = frames_json.get("frames", []) or []

    def to_int(x, default=None):
        if x is None or x == "N/A":
            return default
        try:
            return int(x)
        except Exception:
            return default

    frame_data, timestamps, uses_past, uses_future = [], [], [], []

    for f in frames:
        size_bytes = int(f.get("pkt_size", 0) or 0)
        frame_type = f.get("pict_type", "?") or "?"

        # Prefer pkt_pts, else best_effort_timestamp
        pts_ticks = to_int(f.get("pkt_pts")) or to_int(
            f.get("best_effort_timestamp"), 0
        )

        # Timestamp in seconds = pts * (num/den)
        timestamp_sec = (pts_ticks * tb_num / tb_den) if (pts_ticks and tb_den) else 0.0

        # Decode order via packet file offset
        decode_order = None
        pkt_pos = f.get("pkt_pos")
        if pkt_pos not in (None, "N/A"):
            try:
                decode_order = pos_to_decode_idx.get(int(pkt_pos))
            except Exception:
                pass
        if decode_order is None:
            decode_order = len(frame_data)  # fallback

        # Motion vectors: check if frame references past/future
        mv_past, mv_future = False, False
        for sd in f.get("side_data_list", []) or []:
            if sd.get("side_data_type") == "MOTION_VECTORS":
                for mv in sd.get("motion_vectors", []) or []:
                    mt, src = mv.get("motion_type"), mv.get("source")
                    mt_str, src_str = str(mt).upper() if mt else None, (
                        str(src) if src else None
                    )
                    if mt_str == "L0" or src_str == "0":
                        mv_past = True
                    elif mt_str == "L1" or src_str == "1":
                        mv_future = True

        frame_data.append(
            FrameData(
                size_bytes=size_bytes,
                frame_type=frame_type,
                timestamp=float(timestamp_sec),
                pts=int(pts_ticks or 0),
                decode_order=int(decode_order),
            )
        )
        timestamps.append(float(timestamp_sec))
        uses_past.append(mv_past)
        uses_future.append(mv_future)

    # --- Synthesize timestamps if missing ---
    if (
        not timestamps
        and metadata
        and metadata.total_frames
        and metadata.frames_per_second
    ):
        for i in range(metadata.total_frames):
            t = i / metadata.frames_per_second
            frame_data.append(
                FrameData(
                    size_bytes=0,
                    frame_type="?",
                    timestamp=t,
                    pts=int(round(t * (tb_den / tb_num))) if tb_num else 0,
                    decode_order=i,
                )
            )
            timestamps.append(t)
            uses_past.append(False)
            uses_future.append(False)

    # --- Normalize decode order + ref mapping ---
    if frame_data:
        # Sort frames by decode_order
        sorted_indices = sorted(
            range(len(frame_data)), key=lambda i: (frame_data[i].decode_order, i)
        )
        for new_order, orig_idx in enumerate(sorted_indices):
            frame_data[orig_idx].decode_order = new_order

        # Map prev/next I/P frames for reference fallback
        prev_ip, prev_map = None, [None] * len(frame_data)
        for i, fr in enumerate(frame_data):
            prev_map[i] = prev_ip
            if fr.frame_type in {"I", "P"}:
                prev_ip = i

        next_ip, next_map = None, [None] * len(frame_data)
        for i in range(len(frame_data) - 1, -1, -1):
            if frame_data[i].frame_type in {"I", "P"}:
                next_ip = i
            next_map[i] = next_ip

        for i, fr in enumerate(frame_data):
            past = uses_past[i] or fr.frame_type in {"P", "B"}
            fut = uses_future[i] or fr.frame_type == "B"
            fr.ref_prev = prev_map[i] if past else None
            fr.ref_next = next_map[i] if fut else None

    return metadata, frame_data, timestamps


def check_ffmpeg() -> Tuple[bool, bool]:
    """Return tuple (ffmpeg_ok, ffprobe_ok)."""
    ffmpeg_ok = _run_ffmpeg_cmd(["ffmpeg", "-version"]) is not None
    ffprobe_ok = _run_ffmpeg_cmd(["ffprobe", "-version"]) is not None
    return ffmpeg_ok, ffprobe_ok


class VideoLoader:
    """Main interface for FFmpeg-based video loading."""

    def __init__(self):
        ffmpeg_ok, ffprobe_ok = check_ffmpeg()
        if not ffmpeg_ok:
            raise VideoLoaderError("FFmpeg not available. Install and add to PATH.")
        if not ffprobe_ok:
            raise VideoLoaderError("FFprobe not available. Install and add to PATH.")

    def load_video_file(
        self, file_path: str, log_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[Optional[VideoMetadata], LazyVideoFrameCollection]:
        """Load a video file + metadata, return LazyVideoFrameCollection for frames."""
        if log_callback:
            log_callback("Using FFmpeg for video processing...")

        metadata, frame_meta, timestamps = parse_frames(file_path)
        return metadata, LazyVideoFrameCollection(
            file_path, timestamps, frame_meta, log_callback=log_callback
        )
