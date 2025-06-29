import subprocess
import json
import sys

def parse_gops(file_path):
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

    gops = []
    current_gop = []

    for frame in data['frames']:
        if frame.get("media_type") != "video":
            continue

        ftype = frame.get("pict_type", "?")

        if ftype == "I":
            if current_gop:
                gops.append(current_gop)
            current_gop = ["I"]
        else:
            current_gop.append(ftype)

    if current_gop:
        gops.append(current_gop)

    # Print summary
    print(f"\n🎬 GOP Breakdown for: {file_path}")
    print("-" * 40)
    for i, gop in enumerate(gops):
        print(f"GOP {i}: {len(gop)} frames ({' '.join(gop)})")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gop.py <video.mp4>")
        sys.exit(1)

    parse_gops(sys.argv[1])