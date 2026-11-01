"""Standalone CLI Runner for Automated Evaluation & Accuracy Benchmark Suite.

Executes detection and 3D distance accuracy benchmarks across all calibrated scenes,
validates mathematically bounded error tolerances (<5%), and outputs structured
`benchmark_results.json` and formatted ASCII summary tables.

Usage:
    python benchmarks/run_benchmarks.py [--output benchmark_results.json] [--verbose]
"""

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path so backend and benchmarks modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.distance_estimator import DistanceEstimatorService
from backend.services.yolo_detector import YOLODetectorService
from benchmarks.calibrated_scenes import CalibratedSceneRegistry, get_all_calibrated_scenes
from benchmarks.evaluators import (
    BenchmarkSummary,
    compute_iou,
    evaluate_detections,
    evaluate_distance,
    measure_latency,
)


class BenchmarkRunner:
    """Executes evaluation benchmarks across calibrated scenes."""

    def __init__(
        self,
        output_file: Optional[Path] = None,
        reference_dir: Optional[Path] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        latency_runs: int = 5,
        verbose: bool = False,
    ):
        self.output_file = Path(output_file) if output_file else PROJECT_ROOT / "benchmark_results.json"
        self.reference_dir = Path(reference_dir) if reference_dir else PROJECT_ROOT / "benchmarks" / "reference_data"
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.latency_runs = latency_runs
        self.verbose = verbose

        # Initialize Services
        model_path = PROJECT_ROOT / "yolov8n.pt"
        model_name = str(model_path) if model_path.exists() else "yolov8n.pt"
        self.detector = YOLODetectorService(model_name=model_name)
        self.distance_service = DistanceEstimatorService()

        # Initialize Reference Scenes
        self.registry = CalibratedSceneRegistry(output_dir=self.reference_dir)
        self.scenes = self.registry.scenes

    def run(self) -> Dict[str, Any]:
        """Execute complete benchmark suite and return structured results."""
        start_time = time.time()
        per_scene_results: Dict[str, Any] = {}
        all_distance_evals = []
        all_detection_evals = []
        all_latencies = []

        print("=" * 80)
        print("  YOLO OBJECT DETECTION & 3D DISTANCE ACCURACY BENCHMARK SUITE")
        print("=" * 80)
        print(f"Project Root     : {PROJECT_ROOT}")
        print(f"YOLO Model       : {self.detector.model_name} (Loaded: {self.detector.is_loaded})")
        print(f"Reference Scenes : {len(self.scenes)} calibrated scenes generated")
        print(f"Output Artifact  : {self.output_file}")
        print("-" * 80)

        for scene_key, scene in self.scenes.items():
            if self.verbose:
                print(f"\n[Evaluating Scene: {scene.name}] {scene.description}")

            # 1. Measure real inference latency on scene image
            latency_metrics = measure_latency(
                lambda: self.detector.detect(
                    str(scene.image_path),
                    conf_threshold=self.conf_threshold,
                    iou_threshold=self.iou_threshold,
                ),
                runs=self.latency_runs,
                warmup=1,
            )
            all_latencies.append(latency_metrics["mean_ms"])

            # 2. Run detection
            detect_output = self.detector.detect(
                str(scene.image_path),
                conf_threshold=self.conf_threshold,
                iou_threshold=self.iou_threshold,
            )
            predicted_detections = detect_output.get("detections", [])

            # 3. Evaluate detection metrics against ground truth
            det_eval = evaluate_detections(
                predictions=predicted_detections,
                ground_truths=scene.objects,
                iou_threshold=self.iou_threshold,
            )
            all_detection_evals.append(det_eval)

            # 4. Evaluate 3D distance estimation against analytical ground truth
            distance_eval_list = []
            for pair in scene.distance_pairs:
                obj_a_gt = scene.get_object(pair.object_a_id)
                obj_b_gt = scene.get_object(pair.object_b_id)

                if not obj_a_gt or not obj_b_gt:
                    continue

                # Prepare payload for distance estimator service
                payload_obj_a = {
                    "id": obj_a_gt.id,
                    "class_name": obj_a_gt.class_name,
                    "class": obj_a_gt.class_name,
                    "height": obj_a_gt.height,
                    "width": obj_a_gt.width,
                    "center": list(obj_a_gt.center),
                    "bbox": obj_a_gt.bbox,
                }
                payload_obj_b = {
                    "id": obj_b_gt.id,
                    "class_name": obj_b_gt.class_name,
                    "class": obj_b_gt.class_name,
                    "height": obj_b_gt.height,
                    "width": obj_b_gt.width,
                    "center": list(obj_b_gt.center),
                    "bbox": obj_b_gt.bbox,
                }

                dist_calc = self.distance_service.calculate_distance(
                    object_a=payload_obj_a,
                    object_b=payload_obj_b,
                    image_dimensions={"width": scene.width, "height": scene.height},
                    focal_length_px=scene.focal_length_px,
                    custom_ref_height_a=obj_a_gt.real_height_m,
                    custom_ref_height_b=obj_b_gt.real_height_m,
                )

                dist_eval = evaluate_distance(
                    predicted_result=dist_calc,
                    ground_truth_pair=pair,
                    obj_a_gt=obj_a_gt,
                    obj_b_gt=obj_b_gt,
                    tolerance_pct=pair.tolerance_pct,
                )
                distance_eval_list.append(dist_eval)
                all_distance_evals.append(dist_eval)

            per_scene_results[scene_key] = {
                "scene_name": scene.name,
                "description": scene.description,
                "filename": scene.filename,
                "dimensions": {"width": scene.width, "height": scene.height},
                "focal_length_px": scene.focal_length_px,
                "latency_metrics": latency_metrics,
                "detection_metrics": det_eval.to_dict(),
                "distance_evaluations": [d.to_dict() for d in distance_eval_list],
            }

        # Aggregate Overall Metrics
        total_gt_objects = sum(d.ground_truth_count for d in all_detection_evals)
        total_predictions = sum(d.predicted_count for d in all_detection_evals)
        total_tp = sum(d.true_positives for d in all_detection_evals)
        total_fp = sum(d.false_positives for d in all_detection_evals)
        total_fn = sum(d.false_negatives for d in all_detection_evals)

        overall_precision = round(total_tp / (total_tp + total_fp), 4) if (total_tp + total_fp) > 0 else 0.0
        overall_recall = round(total_tp / total_gt_objects, 4) if total_gt_objects > 0 else 0.0
        overall_f1 = round(
            2.0 * overall_precision * overall_recall / (overall_precision + overall_recall), 4
        ) if (overall_precision + overall_recall) > 0 else 0.0
        overall_map50 = round(sum(d.map50 for d in all_detection_evals) / len(all_detection_evals), 4) if all_detection_evals else 0.0
        mean_latency = round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 0.0

        # Distance tolerances
        passed_pairs = [d for d in all_distance_evals if d.within_tolerance]
        dist_errors_m = [d.distance_3d_error_m for d in all_distance_evals]
        dist_errors_pct = [d.distance_3d_error_pct for d in all_distance_evals]
        mean_dist_err_m = round(sum(dist_errors_m) / len(dist_errors_m), 4) if dist_errors_m else 0.0
        mean_dist_err_pct = round(sum(dist_errors_pct) / len(dist_errors_pct), 2) if dist_errors_pct else 0.0
        max_dist_err_pct = max(dist_errors_pct) if dist_errors_pct else 0.0

        pass_rate = round((len(passed_pairs) / len(all_distance_evals) * 100.0), 1) if all_distance_evals else 100.0
        all_passed = (len(passed_pairs) == len(all_distance_evals))

        overall_summary = BenchmarkSummary(
            total_scenes=len(self.scenes),
            total_ground_truth_objects=total_gt_objects,
            total_predictions=total_predictions,
            mean_inference_time_ms=mean_latency,
            precision=overall_precision,
            recall=overall_recall,
            f1_score=overall_f1,
            map50=overall_map50,
            mean_iou=round(
                sum(d.mean_iou for d in all_detection_evals if d.mean_iou > 0) /
                max(1, len([d for d in all_detection_evals if d.mean_iou > 0])), 4
            ),
            total_distance_pairs_tested=len(all_distance_evals),
            passed_distance_pairs=len(passed_pairs),
            mean_distance_error_m=mean_dist_err_m,
            mean_distance_error_pct=mean_dist_err_pct,
            max_distance_error_pct=max_dist_err_pct,
            distance_tolerance_pass_rate_pct=pass_rate,
            all_tolerances_passed=all_passed,
        )

        total_duration = round(time.time() - start_time, 2)

        benchmark_data = {
            "version": "1.0.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "execution_time_seconds": total_duration,
            "system_info": {
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "yolo_model": self.detector.model_name,
                "yolo_loaded": self.detector.is_loaded,
            },
            "overall_metrics": overall_summary.to_dict(),
            "per_scene_breakdown": per_scene_results,
        }

        # Write structured JSON artifact
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(benchmark_data, f, indent=2)

        self._print_summary_tables(overall_summary, per_scene_results, all_distance_evals)
        return benchmark_data

    def _print_summary_tables(
        self,
        summary: BenchmarkSummary,
        scenes: Dict[str, Any],
        distance_evals: List[Any],
    ):
        """Format and print ASCII summary tables."""
        print("\n" + "=" * 90)
        print("  1. SCENE LATENCY & DETECTION BENCHMARK SUMMARY")
        print("=" * 90)
        print(f"{'Scene Name':<24} | {'Dims':<10} | {'GT':<4} | {'Pred':<5} | {'Mean Latency':<14} | {'P95 Latency':<12}")
        print("-" * 90)
        for key, sc in scenes.items():
            name = sc["scene_name"][:22]
            dims = f"{sc['dimensions']['width']}x{sc['dimensions']['height']}"
            gt_n = sc["detection_metrics"]["ground_truth_count"]
            pr_n = sc["detection_metrics"]["predicted_count"]
            mean_lat = f"{sc['latency_metrics']['mean_ms']:.2f} ms"
            p95_lat = f"{sc['latency_metrics']['p95_ms']:.2f} ms"
            print(f"{name:<24} | {dims:<10} | {gt_n:<4} | {pr_n:<5} | {mean_lat:<14} | {p95_lat:<12}")

        print("\n" + "=" * 90)
        print("  2. MONOCULAR 3D RELATIVE DISTANCE ACCURACY & TOLERANCE VERIFICATION")
        print("=" * 90)
        header = f"{'Pair ID':<26} | {'GT (m)':<8} | {'Est (m)':<8} | {'Err (m)':<8} | {'Err (%)':<8} | {'Tol (%)':<8} | {'Status':<6}"
        print(header)
        print("-" * 90)
        for d in distance_evals:
            pair_name = d.pair_id[:24]
            gt_m = f"{d.ground_truth_distance_3d_m:.2f}m"
            est_m = f"{d.estimated_distance_3d_m:.2f}m"
            err_m = f"{d.distance_3d_error_m:.3f}m"
            err_pct = f"{d.distance_3d_error_pct:.2f}%"
            tol_pct = f"< {d.tolerance_pct:.1f}%"
            status = "PASS" if d.within_tolerance else "FAIL"
            print(f"{pair_name:<26} | {gt_m:<8} | {est_m:<8} | {err_m:<8} | {err_pct:<8} | {tol_pct:<8} | {status:<6}")

        print("\n" + "=" * 90)
        print("  3. CONSOLIDATED BENCHMARK SCORECARD")
        print("=" * 90)
        print(f"Total Reference Scenes Evaluated   : {summary.total_scenes}")
        print(f"Mean Inference Time (per frame)    : {summary.mean_inference_time_ms:.2f} ms")
        print(f"Total Distance Pairs Tested        : {summary.total_distance_pairs_tested}")
        print(f"Distance Pairs Within Tolerance    : {summary.passed_distance_pairs} / {summary.total_distance_pairs_tested}")
        print(f"Mean 3D Distance Estimation Error  : {summary.mean_distance_error_m:.4f} m ({summary.mean_distance_error_pct:.2f}%)")
        print(f"Max 3D Distance Estimation Error   : {summary.max_distance_error_pct:.2f}%")
        print(f"Tolerance Pass Rate                : {summary.distance_tolerance_pass_rate_pct:.1f}%")
        verdict = "PASSED" if summary.all_tolerances_passed else "FAILED"
        print(f"Overall Benchmark Status           : [{verdict}]")
        print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run YOLO & Monocular Distance Benchmark Suite.")
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=str(PROJECT_ROOT / "benchmark_results.json"),
        help="Path to export benchmark_results.json"
    )
    parser.add_argument(
        "--reference-dir",
        type=str,
        default=str(PROJECT_ROOT / "benchmarks" / "reference_data"),
        help="Directory to save generated reference images"
    )
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    parser.add_argument("--iou", type=float, default=0.45, help="YOLO IoU threshold")
    parser.add_argument("--runs", type=int, default=5, help="Latency measurement runs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    runner = BenchmarkRunner(
        output_file=Path(args.output),
        reference_dir=Path(args.reference_dir),
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        latency_runs=args.runs,
        verbose=args.verbose,
    )

    results = runner.run()
    passed = results.get("overall_metrics", {}).get("status") == "PASSED"
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
