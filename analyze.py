import ffmpeg
import sys

def format_bitrate(bps):
    bps = int(bps)
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mbps"
    elif bps >= 1_000:
        return f"{bps / 1_000:.2f} kbps"
    return f"{bps} bps"

def summarize_streams(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        print(f"\n🎬 File: {file_path}\n")

        print(f"{'Index':<5} {'Type':<8} {'Codec':<10} {'Resolution':<12} {'FPS':<6} {'Duration':<10} {'Bitrate':<10}")
        print("-" * 70)

        for stream in probe['streams']:
            idx = stream.get('index')
            typ = stream.get('codec_type')
            codec = stream.get('codec_name', 'n/a')

            # Resolution and audio-specific info
            resolution = f"{stream.get('width')}x{stream.get('height')}" if typ == 'video' else stream.get('channel_layout', 'n/a')
            fps = stream.get('r_frame_rate', 'n/a').split('/')

            try:
                fps_val = round(int(fps[0]) / int(fps[1]), 2) if len(fps) == 2 and int(fps[1]) != 0 else 'n/a'
            except:
                fps_val = 'n/a'

            dur = f"{float(stream.get('duration', 0)):.2f}s"
            bitrate = format_bitrate(stream.get('bit_rate', 0))

            print(f"{idx:<5} {typ:<8} {codec:<10} {resolution:<12} {fps_val:<6} {dur:<10} {bitrate:<10}")

    except ffmpeg.Error as e:
        print("❌ ffmpeg error:", e.stderr.decode())
    except Exception as ex:
        print(f"❌ Error: {ex}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python summarize.py <file>")
        sys.exit(1)
    
    summarize_streams(sys.argv[1])