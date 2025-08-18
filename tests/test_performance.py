import time
import psutil
import tempfile
import pytest
from pathlib import Path
from video_loader import VideoLoader, parse_frames
from src.mp4analyzer import parse_mp4_boxes

class PerformanceBenchmark:
    """Helper class to measure performance metrics."""
    
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
            'duration_ms': (end_time - self.start_time) * 1000,
            'memory_delta_mb': (end_memory - self.start_memory) / (1024 * 1024),
            'peak_memory_mb': end_memory / (1024 * 1024)
        }

@pytest.fixture
def sample_video_files():
    """Generate test video files of different sizes."""
    # Check what files actually exist and use them
    candidates = {
        'small': ['test_10mb.mp4', 'test_small.mp4'],
        'medium': ['test_50mb.mp4', 'test_medium.mp4'], 
        'large': ['test_100mb.mp4', 'test_large.mp4']
    }
    
    result = {}
    for size, paths in candidates.items():
        for path in paths:
            if Path(path).exists():
                result[size] = path
                break
    
    return result

def test_video_loading_performance(sample_video_files):
    """Benchmark video loading times across file sizes."""
    results = {}
    
    for size, file_path in sample_video_files.items():
        if not Path(file_path).exists():
            pytest.skip(f"Test file {file_path} not found")
            
        benchmark = PerformanceBenchmark()
        benchmark.start()
        
        loader = VideoLoader()
        metadata, collection = loader.load_video_file(file_path)
        
        metrics = benchmark.stop()
        results[size] = metrics
        
        print(f"{size} file ({Path(file_path).stat().st_size // (1024*1024)}MB): "
              f"{metrics['duration_ms']:.1f}ms, "
              f"{metrics['memory_delta_mb']:.1f}MB memory")
    
    # Assert performance thresholds
    assert results['small']['duration_ms'] < 5000  # < 5 seconds
    assert results['medium']['duration_ms'] < 15000  # < 15 seconds

def test_frame_access_performance(sample_video_files):
    """Benchmark frame access patterns."""
    file_path = sample_video_files['medium']
    if not Path(file_path).exists():
        pytest.skip(f"Test file {file_path} not found")
        
    loader = VideoLoader()
    metadata, collection = loader.load_video_file(file_path)
    
    # Test sequential access
    benchmark = PerformanceBenchmark()
    benchmark.start()
    for i in range(min(10, collection.count)):
        frame = collection.get_frame(i)
    sequential_metrics = benchmark.stop()
    
    # Test random access
    benchmark = PerformanceBenchmark()
    benchmark.start()
    import random
    indices = random.sample(range(collection.count), min(10, collection.count))
    for i in indices:
        frame = collection.get_frame(i)
    random_metrics = benchmark.stop()
    
    print(f"Sequential access: {sequential_metrics['duration_ms']:.1f}ms")
    print(f"Random access: {random_metrics['duration_ms']:.1f}ms")

def test_box_parsing_performance(sample_video_files):
    """Benchmark MP4 box parsing performance."""
    results = {}
    
    for size, file_path in sample_video_files.items():
        if not Path(file_path).exists():
            continue
            
        benchmark = PerformanceBenchmark()
        benchmark.start()
        
        boxes = parse_mp4_boxes(file_path)
        
        metrics = benchmark.stop()
        results[size] = metrics
        
        print(f"Box parsing {size}: {metrics['duration_ms']:.1f}ms, "
              f"{len(boxes)} top-level boxes")