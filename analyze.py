import ffmpeg
import json
import sys

def get_metadata(file_path):
    try:
        print(f"📦 Analyzing: {file_path}")
        metadata = ffmpeg.probe(file_path)
        print(json.dumps(metadata, indent=2))
    except ffmpeg.Error as e:
        print("❌ ffmpeg error:")
        print(e.stderr.decode())
    except Exception as ex:
        print(f"❌ General error: {ex}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <input_file.mp4>")
        sys.exit(1)
    
    video_file = sys.argv[1]
    get_metadata(video_file)