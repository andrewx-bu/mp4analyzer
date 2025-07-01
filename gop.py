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

def parse_gops(file_path):
    try:
        container = av.open(file_path)

        gops = []
        current_gop = []

        for frame in container.decode(video=0):
            ftype = PICT_TYPE_MAP.get(frame.pict_type, '?')

            if ftype == 'I':
                if current_gop:
                    gops.append(current_gop)
                current_gop = ['I']
            else:
                current_gop.append(ftype)

        if current_gop:
            gops.append(current_gop)

        # Print summary
        print(f"\n🎬 GOP Breakdown for: {file_path}")
        print("-" * 40)
        for i, gop in enumerate(gops):
            print(f"GOP {i}: {len(gop)} frames ({' '.join(gop)})")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gop.py <video.mp4>")
        sys.exit(1)

    parse_gops(sys.argv[1])