import av
import sys

def format_bitrate(bps):
    bps = int(bps) if bps else 0
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mbps"
    elif bps >= 1_000:
        return f"{bps / 1_000:.2f} kbps"
    return f"{bps} bps"

def summarize_streams(file_path):
    try:
        container = av.open(file_path)
        print(f"\n🎬 File: {file_path}\n")

        print(f"{'Index':<5} {'Type':<8} {'Codec':<10} {'Resolution':<12} {'FPS':<6} {'Duration':<10} {'Bitrate':<10}")
        print("-" * 70)

        for stream in container.streams:
            idx = stream.index
            typ = stream.type
            codec = stream.codec_context.name

            # Handle resolution/audio channels
            if typ == 'video':
                resolution = f"{stream.width}x{stream.height}"
                fps = stream.base_rate
                fps_val = round(float(fps), 2) if fps else 'n/a'
            else:
                resolution = str(stream.channels) + 'ch'
                fps_val = 'n/a'

            dur = f"{float(stream.duration * stream.time_base):.2f}s" if stream.duration else 'n/a'
            bitrate = format_bitrate(stream.bit_rate)

            print(f"{idx:<5} {typ:<8} {codec:<10} {resolution:<12} {fps_val:<6} {dur:<10} {bitrate:<10}")

    except Exception as ex:
        print(f"❌ Error: {ex}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python summarize.py <file>")
        sys.exit(1)
    
    summarize_streams(sys.argv[1])