import av
import sys

# Map PyAV's pict_type int to str
# https://pyav.org/docs/develop/api/video.html
PICT_TYPE_MAP = {
    0: '?',  # Undefined
    1: 'I',  # Intra
    2: 'P',  # Predicted
    3: 'B',  # Bi-directional predicted
    4: 'S',  # S(GMC)-VOP MPEG-4
    5: 'SI', # Switching intra
    6: 'SP', # Switching predicted
    7: 'BI', # BI type
}

def get_video_frames(file_path):
    try:
        container = av.open(file_path)
        video_stream = next(s for s in container.streams if s.type == 'video')

        print(f"\n🎬 Frame Timeline for: {file_path}\n")
        print(f"{'Index':<6} {'Type':<6} {'PTS':<10} {'Key Frame':<10}")
        print("-" * 40)

        for i, frame in enumerate(container.decode(video=0)):
            ftype = PICT_TYPE_MAP.get(frame.pict_type, '?')
            pts = float(frame.pts * video_stream.time_base)
            key = "Yes" if frame.key_frame else "No"

            print(f"{i:<6} {ftype:<6} {pts:<10.3f} {key:<10}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python frames.py <input_file>")
        sys.exit(1)

    get_video_frames(sys.argv[1])