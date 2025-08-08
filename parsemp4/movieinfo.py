from __future__ import annotations

import subprocess
import json
import os
import struct
from typing import List

from .boxes import MP4Box, MovieHeaderBox


def _run_ffprobe(cmd: List[str]) -> dict:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        if result.returncode != 0:
            return {}
        return json.loads(result.stdout)
    except Exception:
        return {}


def _find_box(boxes: List[MP4Box], box_type: str) -> MP4Box | None:
    for box in boxes:
        if box.type == box_type:
            return box
        child = _find_box(box.children, box_type)
        if child:
            return child
    return None


def _parse_mvhd(box: MP4Box) -> tuple[int, int]:
    if not box:
        return 0, 0
    if isinstance(box, MovieHeaderBox):
        return box.timescale, box.duration
    if not box.data:
        return 0, 0
    data = box.data
    version = data[0]
    if version == 1:
        timescale = struct.unpack('>I', data[20:24])[0]
        duration = struct.unpack('>Q', data[24:32])[0]
    else:
        timescale = struct.unpack('>I', data[12:16])[0]
        duration = struct.unpack('>I', data[16:20])[0]
    return timescale, duration


def _format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02}:{secs:06.3f}"


def generate_movie_info(file_path: str, boxes: List[MP4Box]) -> str:
    """Generate detailed movie information text from ffprobe and MP4 boxes."""
    data = _run_ffprobe([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-show_format', file_path
    ])

    format_info = data.get('format', {})
    streams = data.get('streams', [])

    file_size = int(format_info.get('size', 0))
    bit_rate = int(format_info.get('bit_rate', 0))
    duration_sec = float(format_info.get('duration', 0.0))

    mvhd = _find_box(boxes, 'mvhd')
    timescale, duration_units = _parse_mvhd(mvhd)
    if duration_sec == 0 and timescale:
        duration_sec = duration_units / timescale if timescale else 0
    if bit_rate == 0 and duration_sec > 0:
        bit_rate = int(file_size * 8 / duration_sec)

    tags = format_info.get('tags', {})
    major_brand = tags.get('major_brand', '')
    compat = tags.get('compatible_brands', '')
    compat_list = [compat[i:i+4] for i in range(0, len(compat), 4)] if compat else []

    codecs = []
    for s in streams:
        codec = s.get('codec_tag_string') or s.get('codec_name', '')
        if codec:
            codecs.append(codec)
    mime = f"video/mp4; codecs=\"{','.join(codecs)}\"" if codecs else 'video/mp4'

    fragmented = any(b.type in {'moof', 'mvex'} for b in boxes)
    progressive = False
    iod = _find_box(boxes, 'iods') is not None

    creation_time = tags.get('creation_time', '')
    modification_time = tags.get('modification_time', '')

    lines: List[str] = []
    lines.append('Movie Info')
    lines.append(f"File Size / Bitrate\t{file_size} bytes / {bit_rate // 1000} kbps")
    if timescale and duration_units:
        lines.append(
            f"Duration / Timescale\t{duration_units}/{timescale} ({_format_duration(duration_units / timescale)})"
        )
    elif duration_sec:
        lines.append(f"Duration\t{_format_duration(duration_sec)}")
    if major_brand:
        brand_line = [major_brand] + compat_list
        lines.append(f"Brands (major/compatible)\t{','.join(brand_line)}")
    lines.append(f"MIME\t{mime}")
    lines.append(f"Progressive\t{str(progressive).lower()}")
    lines.append(f"Fragmented\t{str(fragmented).lower()}")
    lines.append(f"MPEG-4 IOD\t{str(iod).lower()}")
    if creation_time or modification_time:
        lines.append(
            f"Creation / Modification Dates\t{creation_time} / {modification_time}"
        )
    lines.append('')

    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    if video_streams:
        lines.append('Video track(s) info')
        lines.append('ID\tDuration\tTimescale\tSamples\tBitrate (kbps)\tCodec\tLanguage\tWidth\tHeight')
        for s in video_streams:
            track_id = int(s.get('id', '0'), 0) if s.get('id') else s.get('index', 0)
            time_base = s.get('time_base', '1/1')
            num, den = map(int, time_base.split('/'))
            track_timescale = den // num if num else 0
            dur_units = int(s.get('duration_ts', 0))
            if dur_units == 0 and track_timescale:
                dur_units = int(float(s.get('duration', 0.0)) * track_timescale)
            samples = int(s.get('nb_frames', 0))
            bitrate_k = int(int(s.get('bit_rate', 0)) / 1000)
            codec = s.get('codec_tag_string') or s.get('codec_name', '')
            lang = s.get('tags', {}).get('language', 'und')
            width = s.get('width', 0)
            height = s.get('height', 0)
            lines.append(
                f"{track_id}\t{dur_units}\t{track_timescale}\t{samples}\t{bitrate_k}\t{codec}\t{lang}\t{width}\t{height}"
            )
        lines.append('')

    audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
    if audio_streams:
        lines.append('Audio track(s) info')
        lines.append('ID\tDuration\tTimescale\tSamples\tBitrate (kbps)\tCodec\tLanguage\tSample Rate\tChannel Count')
        for s in audio_streams:
            track_id = int(s.get('id', '0'), 0) if s.get('id') else s.get('index', 0)
            time_base = s.get('time_base', '1/1')
            num, den = map(int, time_base.split('/'))
            track_timescale = den // num if num else 0
            dur_units = int(s.get('duration_ts', 0))
            if dur_units == 0 and track_timescale:
                dur_units = int(float(s.get('duration', 0.0)) * track_timescale)
            samples = int(s.get('nb_frames', 0))
            bitrate_k = int(int(s.get('bit_rate', 0)) / 1000)
            codec = s.get('codec_tag_string') or s.get('codec_name', '')
            lang = s.get('tags', {}).get('language', 'und')
            sample_rate = s.get('sample_rate', '0')
            channels = s.get('channels', 0)
            lines.append(
                f"{track_id}\t{dur_units}\t{track_timescale}\t{samples}\t{bitrate_k}\t{codec}\t{lang}\t{sample_rate}\t{channels}"
            )

    return '\n'.join(lines)