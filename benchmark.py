#!/usr/bin/env python3
"""
Runs performance tests (box parsing, video loading, frame access)
on a given MP4 file and reports timing, memory usage, and counts.
Usage: python benchmark.py video.mp4 [results.json] [label]
"""

import argparse
import json
import time
import psutil
from pathlib import Path
from video_loader import VideoLoader
from src.mp4analyzer import parse_mp4_boxes


def run_benchmark(video_file: str) -> dict:
    """Run comprehensive benchmark on a video file."""
    results = {}

    # 1. Box parsing benchmark
    start = time.perf_counter()
    start_mem = psutil.Process().memory_info().rss

    boxes = parse_mp4_boxes(video_file)

    results["box_parsing"] = {
        "duration_ms": (time.perf_counter() - start) * 1000,
        "memory_mb": (psutil.Process().memory_info().rss - start_mem) / (1024 * 1024),
        "box_count": len(boxes),
    }

    # 2. Video loading benchmark
    start = time.perf_counter()
    start_mem = psutil.Process().memory_info().rss

    loader = VideoLoader()
    _, collection = loader.load_video_file(video_file)

    results["video_loading"] = {
        "duration_ms": (time.perf_counter() - start) * 1000,
        "memory_mb": (psutil.Process().memory_info().rss - start_mem) / (1024 * 1024),
        "frame_count": collection.count if collection else 0,
    }

    # 3. Frame access benchmark
    if collection and collection.count > 0:
        start = time.perf_counter()
        start_mem = psutil.Process().memory_info().rss

        # Access first 10 frames
        for i in range(min(10, collection.count)):
            collection.get_frame(i)

        results["frame_access"] = {
            "duration_ms": (time.perf_counter() - start) * 1000,
            "memory_mb": (psutil.Process().memory_info().rss - start_mem)
            / (1024 * 1024),
            "frames_accessed": min(10, collection.count),
        }

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark MP4 analysis and video loading performance."
    )
    parser.add_argument("file", help="Video file to benchmark")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Optional JSON file to save results (if omitted, results are printed)",
    )
    parser.add_argument(
        "label",
        nargs="?",
        default="benchmark",
        help="Optional label for this run (default: 'benchmark')",
    )

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File {args.file} not found")
        return 1

    print(f"Running benchmark on {args.file}...")
    results = run_benchmark(args.file)

    # Add metadata
    results["file_info"] = {
        "path": args.file,
        "size_mb": Path(args.file).stat().st_size / (1024 * 1024),
        "label": args.label,
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
