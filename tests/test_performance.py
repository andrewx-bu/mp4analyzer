import time
import random
from pathlib import Path

import psutil
import pytest

from video_loader import VideoLoader
from src.mp4analyzer import parse_mp4_boxes


# ----------------------------
# Configurable thresholds (ms)
# ----------------------------
LOAD_THRESHOLDS_MS = {
    "small": 5_000,  # < 5s
    "medium": 15_000,  # < 15s
    "large": 45_000,  # < 45s (looser, big files vary a lot)
}

BOX_PARSE_THRESHOLDS_MS = {
    "small": 2_500,
    "medium": 7_500,
    "large": 20_000,
}

# Number of frames to touch during access tests
FRAME_ACCESS_COUNT = 10


class PerformanceBenchmark:
    """Stopwatch + RSS memory sampler using psutil."""

    def __init__(self):
        self.start_time = None
        self.start_memory = None

    def start(self):
        self.start_time = time.perf_counter()
        self.start_memory = psutil.Process().memory_info().rss

    def stop(self):
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss
        return {
            "duration_ms": (end_time - self.start_time) * 1000,
            "memory_delta_mb": (end_memory - self.start_memory) / (1024 * 1024),
            # Note: this is *current* RSS at stop, not true peak.
            "rss_mb": end_memory / (1024 * 1024),
        }


def first_existing_path(candidates) -> Path | None:
    """Return the first existing Path from a list of string paths, else None."""
    for p in candidates:
        path = Path(p)
        if path.exists():
            return path
    return None


@pytest.mark.performance
@pytest.mark.parametrize(
    "size,candidates",
    [
        ("small", ["test_10mb.mp4", "test_small.mp4"]),
        ("medium", ["test_50mb.mp4", "test_medium.mp4"]),
        ("large", ["test_100mb.mp4", "test_large.mp4"]),
    ],
    ids=["small", "medium", "large"],
)
def test_video_loading_performance(size, candidates):
    """Benchmark video loading time & memory by size, skipping if the file isn't present."""
    file_path = first_existing_path(candidates)
    if file_path is None:
        pytest.skip(f"No {size} test file found among {candidates}")

    benchmark = PerformanceBenchmark()
    benchmark.start()

    loader = VideoLoader()
    loader.load_video_file(str(file_path))

    metrics = benchmark.stop()

    file_mb = file_path.stat().st_size // (1024 * 1024)
    print(
        f"{size} file ({file_mb}MB): "
        f"{metrics['duration_ms']:.1f}ms, "
        f"{metrics['memory_delta_mb']:.1f}MB delta, "
        f"RSS {metrics['rss_mb']:.1f}MB"
    )

    # Assert performance threshold for this size (if configured)
    if size in LOAD_THRESHOLDS_MS:
        assert (
            metrics["duration_ms"] < LOAD_THRESHOLDS_MS[size]
        ), f"Load too slow for {size}: {metrics['duration_ms']:.1f}ms >= {LOAD_THRESHOLDS_MS[size]}ms"


@pytest.mark.performance
def test_frame_access_performance():
    """Benchmark sequential vs random frame access on the 'medium' file, skip if missing."""
    candidates = ["test_50mb.mp4", "test_medium.mp4"]
    file_path = first_existing_path(candidates)
    if file_path is None:
        pytest.skip(f"No medium test file found among {candidates}")

    loader = VideoLoader()
    _, collection = loader.load_video_file(str(file_path))

    if not collection or collection.count <= 0:
        pytest.skip("No frames available to test access performance")

    n = min(FRAME_ACCESS_COUNT, collection.count)

    # Deterministic randomness to reduce flakiness
    random.seed(0)

    # Sequential access
    bench_seq = PerformanceBenchmark()
    bench_seq.start()
    for i in range(n):
        _ = collection.get_frame(i)
    seq_metrics = bench_seq.stop()

    # Random access
    bench_rand = PerformanceBenchmark()
    bench_rand.start()
    indices = random.sample(range(collection.count), n)
    for i in indices:
        _ = collection.get_frame(i)
    rand_metrics = bench_rand.stop()

    print(
        f"Sequential access ({n} frames): {seq_metrics['duration_ms']:.1f}ms | "
        f"Random access ({n} frames): {rand_metrics['duration_ms']:.1f}ms"
    )

    # Optional: require sequential to be no slower than, say, 2* random (very loose)
    # This is intentionally lenient because caching/decoding strategies vary.
    assert seq_metrics["duration_ms"] <= rand_metrics["duration_ms"] * 2.0 + 5_000


@pytest.mark.performance
@pytest.mark.parametrize(
    "size,candidates",
    [
        ("small", ["test_10mb.mp4", "test_small.mp4"]),
        ("medium", ["test_50mb.mp4", "test_medium.mp4"]),
        ("large", ["test_100mb.mp4", "test_large.mp4"]),
    ],
    ids=["small", "medium", "large"],
)
def test_box_parsing_performance(size, candidates):
    """Benchmark MP4 box parsing performance by size, skipping if the file isn't present."""
    file_path = first_existing_path(candidates)
    if file_path is None:
        pytest.skip(f"No {size} test file found among {candidates}")

    bench = PerformanceBenchmark()
    bench.start()

    boxes = parse_mp4_boxes(str(file_path))

    metrics = bench.stop()

    print(
        f"Box parsing {size}: {metrics['duration_ms']:.1f}ms, "
        f"{len(boxes)} top-level boxes, RSS {metrics['rss_mb']:.1f}MB"
    )

    if size in BOX_PARSE_THRESHOLDS_MS:
        assert (
            metrics["duration_ms"] < BOX_PARSE_THRESHOLDS_MS[size]
        ), f"Box parsing too slow for {size}: {metrics['duration_ms']:.1f}ms >= {BOX_PARSE_THRESHOLDS_MS[size]}ms"
