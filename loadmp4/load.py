import av
from dataclasses import dataclass
from typing import Optional

@dataclass
class VideoInfo:
    path: str
    duration: float
    width: int
    height: int
    codec: str
    frame_count: int
    fps: float

class MP4Loader:
    @staticmethod
    def load_video(file_path: str) -> Optional[VideoInfo]:
        try:
            with av.open(file_path) as container:
                video_stream = next(s for s in container.streams if s.type == 'video')
                
                return VideoInfo(
                    path=file_path,
                    duration=float(video_stream.duration * video_stream.time_base),
                    width=video_stream.width,
                    height=video_stream.height,
                    codec=video_stream.codec_context.name,
                    frame_count=video_stream.frames,
                    fps=float(video_stream.base_rate)
                )
        except Exception as e:
            print(f"Error loading video: {e}")
            return None