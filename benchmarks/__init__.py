"""Automated Evaluation & Accuracy Benchmark Suite for YOLO Object Distance System.

Provides programmatic generation of calibrated ground-truth scenes,
metric evaluators (IoU, Precision, Recall, mAP50, latency, 3D Euclidean distance error),
and automated runner producing benchmark_results.json.
"""

from benchmarks.calibrated_scenes import (
    CalibratedScene,
    CalibratedSceneRegistry,
    get_all_calibrated_scenes,
)
from benchmarks.evaluators import (
    compute_iou,
    compute_ap50,
    evaluate_detections,
    evaluate_distance,
    measure_latency,
    BenchmarkSummary,
)
from benchmarks.run_benchmarks import BenchmarkRunner, main

__all__ = [
    "CalibratedScene",
    "CalibratedSceneRegistry",
    "get_all_calibrated_scenes",
    "compute_iou",
    "compute_ap50",
    "evaluate_detections",
    "evaluate_distance",
    "measure_latency",
    "BenchmarkSummary",
    "BenchmarkRunner",
    "main",
]
