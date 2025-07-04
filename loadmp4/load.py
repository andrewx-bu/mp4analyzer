import av
from typing import Optional
from dataclasses import dataclass

@dataclass
class VideoInfo:
    """
    Holds metadata information about a loaded video.

    Attributes:
        path: File path of the video.
        duration: Duration of the video in seconds.
        width: Width of the video frames in pixels.
        height: Height of the video frames in pixels.
        codec: Codec name (e.g., 'h264').
        frame_count: Total number of frames in the video stream.
        fps: Frames per second of the video.
    """
    path: str
    duration: float
    width: int
    height: int
    codec: str
    frame_count: int
    fps: float

class MP4Loader:
    """
    Provides functionality to load and extract metadata from MP4 video files.
    """

    @staticmethod
    def load_video(file_path: str) -> Optional[VideoInfo]:
        """
        Attempts to open the given video file and extract metadata.

        Parameters:
            file_path: Path to the MP4 file to load.

        Returns:
            A VideoInfo object if successful, None otherwise.
        """
        try:
            # Open container and locate video stream
            with av.open(file_path) as container:
                video_stream = next((s for s in container.streams if s.type == 'video'), None)
                if video_stream is None:
                    print(f"No video stream found in {file_path}")
                    return None

                # Compute duration and frame rate
                duration = float(video_stream.duration * video_stream.time_base)
                fps = float(video_stream.base_rate)

                # Return gathered metadata
                return VideoInfo(
                    path=file_path,
                    duration=duration,
                    width=video_stream.width,
                    height=video_stream.height,
                    codec=video_stream.codec_context.name,
                    frame_count=video_stream.frames,
                    fps=fps
                )
        except Exception as e:
            print(f"Error loading video: {e}")
            return None