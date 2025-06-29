import subprocess
import json
import sys

def get_video_frames(file_path):
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v",
            "-show_frames",
            "-print_format", "json",
            file_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        data = json.loads(result.stdout)

        print(f"\n🎞️ Frame Timeline for: {file_path}\n")
        print(f"{'Index':<6} {'Type':<6} {'PTS':<10} {'Key Frame':<10}")
        print("-" * 40)

        for i, frame in enumerate(data['frames']):
            if frame['media_type'] != 'video':
                continue
            ftype = frame.get('pict_type', '?')
            pts = frame.get('pts_time', 'n/a')
            key = "Yes" if frame.get('key_frame') == 1 else "No"

            print(f"{i:<6} {ftype:<6} {pts:<10} {key:<10}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python frames.py <input_file>")
        sys.exit(1)

    get_video_frames(sys.argv[1])