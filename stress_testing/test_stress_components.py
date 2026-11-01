"""
Component unit tests for stress_testing package:
- LatencyProfiler: percentile math, budget checks, bottleneck profiling
- MemoryTracker: RSS sampling, linear regression slope, leak detection
- ConcurrentRunner: payload creation and endpoint simulation
"""

import math
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stress_testing.latency_profiler import LatencyProfiler, get_cpu_brand_name
from stress_testing.memory_tracker import MemoryTracker
from stress_testing.concurrent_runner import get_test_image_base64, get_test_distance_payload


def test_cpu_brand_detection():
    brand = get_cpu_brand_name()
    assert isinstance(brand, str)
    assert len(brand) > 0
    print(f"[PASS] CPU Brand Detected: {brand}")


def test_latency_profiler_percentiles():
    profiler = LatencyProfiler(target_p95_budget_ms=80.0)
    profiler.start()

    # Simulate 100 requests with controlled latencies: 1ms to 100ms
    for i in range(1, 101):
        profiler.record(
            endpoint="/api/distance",
            latency_ms=float(i),
            status_code=200
        )
    profiler.stop()

    stats = profiler.get_stats_for("/api/distance")
    assert stats["count"] == 100
    assert stats["successful"] == 100
    assert stats["failed"] == 0
    assert stats["unhandled_5xx_count"] == 0
    assert math.isclose(stats["p50_ms"], 50.5, abs_tol=1.5)
    assert math.isclose(stats["p90_ms"], 90.1, abs_tol=1.5)
    assert math.isclose(stats["p95_ms"], 95.05, abs_tol=1.5)
    assert math.isclose(stats["p99_ms"], 99.01, abs_tol=1.5)
    print(f"[PASS] LatencyProfiler Percentiles Verified: P50={stats['p50_ms']}, P95={stats['p95_ms']}")


def test_latency_profiler_bottleneck():
    profiler = LatencyProfiler(target_p95_budget_ms=80.0)
    profiler.start()

    # Case 1: Within budget
    for _ in range(50):
        profiler.record(endpoint="/api/distance", latency_ms=25.0, status_code=200)
    analysis1 = profiler.get_bottleneck_analysis()
    assert analysis1["status"] == "BUDGET_MET"
    assert analysis1["meets_budget"] is True
    print(f"[PASS] LatencyProfiler Budget Met Case Verified: {analysis1['status']}")

    # Case 2: Above budget with YOLO inference
    for _ in range(50):
        profiler.record(endpoint="/api/detect", latency_ms=110.0, status_code=200, inference_time_ms=90.0)
    analysis2 = profiler.get_bottleneck_analysis()
    assert analysis2["status"] == "HARDWARE_CPU_BOUND"
    assert analysis2["latency_breakdown"]["inference_bound_ratio"] > 0.5
    print(f"[PASS] LatencyProfiler Hardware CPU Bound Case Verified: {analysis2['status']}")


def test_memory_tracker_sampling():
    tracker = MemoryTracker(target_pid=os.getpid(), sample_interval_sec=0.1, leak_threshold_mb=50.0)
    with tracker:
        # Allocate some memory temporarily
        chunk = bytearray(10 * 1024 * 1024) # 10 MB
        time.sleep(0.3)
        del chunk

    metrics = tracker.get_metrics()
    assert metrics["baseline_rss_mb"] > 0
    assert metrics["sample_count"] >= 2
    assert metrics["leak_detected"] is False
    assert metrics["status"] == "STABLE"
    print(f"[PASS] MemoryTracker Sampling Verified: baseline={metrics['baseline_rss_mb']}MB, peak={metrics['peak_rss_mb']}MB, leak_detected={metrics['leak_detected']}")


def test_payload_generation():
    b64_img = get_test_image_base64()
    assert isinstance(b64_img, str)
    assert b64_img.startswith("data:image/jpeg;base64,")
    assert len(b64_img) > 100

    dist_payload = get_test_distance_payload()
    assert "object_a" in dist_payload
    assert "object_b" in dist_payload
    assert "image_dimensions" in dist_payload
    print(f"[PASS] Payload Generation Verified (b64 len: {len(b64_img)})")


if __name__ == "__main__":
    test_cpu_brand_detection()
    test_latency_profiler_percentiles()
    test_latency_profiler_bottleneck()
    test_memory_tracker_sampling()
    test_payload_generation()
    print("\nALL STRESS TESTING COMPONENT UNIT TESTS PASSED SUCCESSFULLY!")
