# Module for loading MP4 metadata.
import av
from typing import Optional
from dataclasses import dataclass

@dataclass
class VideoInfo:
    # Holds metadata for a video file.
    path: str
    duration: float
    width: int
    height: int
    codec: str
    frame_count: int
    fps: float

class MP4Loader:
    # Utility to extract metadata from MP4/MOV files.
    @staticmethod
    def load_video(path: str) -> Optional[VideoInfo]:
        """
        Open the video container and extract stream info.
        args: Filesystem path to the video.
        returns: VideoInfo if successful, else None.
        """
        try:
            container = av.open(path)
            video_stream = next((s for s in container.streams if s.type == 'video'), None)
            if not video_stream:
                return None

            # Duration in seconds
            duration = float(video_stream.duration * video_stream.time_base)
            fps = float(video_stream.base_rate)

            return VideoInfo(
                path=path,
                duration=duration,
                width=video_stream.width,
                height=video_stream.height,
                codec=video_stream.codec_context.name,
                frame_count=video_stream.frames,
                fps=fps
            )
        except Exception:
            return None