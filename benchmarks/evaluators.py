"""Evaluation Metrics and Ground-Truth Verifier for YOLO Object Distance System.

Computes:
- Intersection over Union (IoU)
- Detection metrics: True/False Positives, Precision, Recall, F1-Score, mAP@50
- High-resolution inference latency profiling (mean, min, max, P95)
- Monocular 3D Euclidean relative distance error and tolerance verification (<5% tolerance)
"""

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


def compute_iou(
    box_a: Union[List[Union[int, float]], Tuple[Union[int, float], ...]],
    box_b: Union[List[Union[int, float]], Tuple[Union[int, float], ...]]
) -> float:
    """Calculate Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    if not box_a or not box_b or len(box_a) < 4 or len(box_b) < 4:
        return 0.0

    ax1, ay1, ax2, ay2 = float(box_a[0]), float(box_a[1]), float(box_a[2]), float(box_a[3])
    bx1, by1, bx2, by2 = float(box_b[0]), float(box_b[1]), float(box_b[2]), float(box_b[3])

    # Ensure coordinates are ordered
    if ax1 > ax2:
        ax1, ax2 = ax2, ax1
    if ay1 > ay2:
        ay1, ay2 = ay2, ay1
    if bx1 > bx2:
        bx1, bx2 = bx2, bx1
    if by1 > by2:
        by1, by2 = by2, by1

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0

    return round(float(inter_area / union_area), 4)


def compute_ap50(
    recalls: List[float],
    precisions: List[float]
) -> float:
    """Compute Average Precision at 0.5 IoU (AP50) using 11-point interpolation."""
    if not recalls or not precisions:
        return 0.0

    ap = 0.0
    for t in np_linspace(0.0, 1.0, 11):
        # Precision at recall >= t
        prec_candidates = [p for r, p in zip(recalls, precisions) if r >= t]
        p_at_t = max(prec_candidates) if prec_candidates else 0.0
        ap += p_at_t / 11.0
    return round(float(ap), 4)


def np_linspace(start: float, stop: float, num: int) -> List[float]:
    """Pure-python linspace helper."""
    if num <= 1:
        return [start]
    step = (stop - start) / (num - 1)
    return [round(start + i * step, 4) for i in range(num)]


@dataclass
class DetectionEvaluationResult:
    """Results of object detection evaluation against ground truth annotations."""
    ground_truth_count: int
    predicted_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    map50: float
    mean_iou: float
    matched_pairs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ground_truth_count": self.ground_truth_count,
            "predicted_count": self.predicted_count,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "map50": self.map50,
            "mean_iou": self.mean_iou,
            "matched_pairs": self.matched_pairs,
        }


def evaluate_detections(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Any],
    iou_threshold: float = 0.50
) -> DetectionEvaluationResult:
    """Evaluate predicted detections against ground truth objects."""
    gt_list = []
    for g in ground_truths:
        if hasattr(g, "bbox"):
            gt_list.append({
                "id": getattr(g, "id", "gt"),
                "class_name": getattr(g, "class_name", "object"),
                "bbox": getattr(g, "bbox", [0, 0, 0, 0])
            })
        elif isinstance(g, dict):
            gt_list.append(g)

    gt_count = len(gt_list)
    pred_count = len(predictions)

    if gt_count == 0 and pred_count == 0:
        return DetectionEvaluationResult(
            ground_truth_count=0,
            predicted_count=0,
            true_positives=0,
            false_positives=0,
            false_negatives=0,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            map50=1.0,
            mean_iou=1.0,
        )

    if gt_count == 0 and pred_count > 0:
        return DetectionEvaluationResult(
            ground_truth_count=0,
            predicted_count=pred_count,
            true_positives=0,
            false_positives=pred_count,
            false_negatives=0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            map50=0.0,
            mean_iou=0.0,
        )

    if gt_count > 0 and pred_count == 0:
        return DetectionEvaluationResult(
            ground_truth_count=gt_count,
            predicted_count=0,
            true_positives=0,
            false_positives=0,
            false_negatives=gt_count,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            map50=0.0,
            mean_iou=0.0,
        )

    # Sort predictions by confidence descending
    sorted_preds = sorted(
        predictions,
        key=lambda p: float(p.get("confidence", 1.0)),
        reverse=True
    )

    matched_gt_indices = set()
    true_positives = 0
    false_positives = 0
    ious_matched = []
    matched_pairs = []

    cum_recalls = []
    cum_precisions = []

    for pred in sorted_preds:
        p_box = pred.get("bbox") or pred.get("box_coords", [0, 0, 0, 0])
        p_cls = str(pred.get("class_name") or pred.get("class") or "").lower()

        best_iou = 0.0
        best_gt_idx = -1

        for gt_idx, gt in enumerate(gt_list):
            if gt_idx in matched_gt_indices:
                continue
            gt_box = gt.get("bbox") or [0, 0, 0, 0]
            gt_cls = str(gt.get("class_name") or gt.get("class") or "").lower()

            # Optional class matching (allow matching if classes match or both vehicle/object)
            class_match = (
                p_cls == gt_cls
                or (p_cls in ["car", "truck", "bus"] and gt_cls in ["car", "truck", "bus"])
                or not p_cls or not gt_cls
            )
            if not class_match:
                continue

            iou = compute_iou(p_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx

        if best_iou >= iou_threshold and best_gt_idx >= 0:
            true_positives += 1
            matched_gt_indices.add(best_gt_idx)
            ious_matched.append(best_iou)
            matched_pairs.append({
                "pred_id": pred.get("id"),
                "gt_id": gt_list[best_gt_idx].get("id"),
                "iou": best_iou,
                "pred_bbox": p_box,
                "gt_bbox": gt_list[best_gt_idx].get("bbox"),
            })
        else:
            false_positives += 1

        cur_tp = true_positives
        cur_fp = false_positives
        cur_prec = cur_tp / (cur_tp + cur_fp) if (cur_tp + cur_fp) > 0 else 0.0
        cur_rec = cur_tp / gt_count if gt_count > 0 else 0.0
        cum_precisions.append(cur_prec)
        cum_recalls.append(cur_rec)

    false_negatives = max(0, gt_count - true_positives)

    precision = round(true_positives / (true_positives + false_positives), 4) if (true_positives + false_positives) > 0 else 0.0
    recall = round(true_positives / gt_count, 4) if gt_count > 0 else 0.0
    f1 = round(2.0 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0
    map50 = compute_ap50(cum_recalls, cum_precisions)
    mean_iou = round(sum(ious_matched) / len(ious_matched), 4) if ious_matched else 0.0

    return DetectionEvaluationResult(
        ground_truth_count=gt_count,
        predicted_count=pred_count,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1_score=f1,
        map50=map50,
        mean_iou=mean_iou,
        matched_pairs=matched_pairs,
    )


@dataclass
class DistanceEvaluationResult:
    """Accuracy results of 3D Euclidean distance estimation against analytical ground truth."""
    pair_id: str
    object_a_id: str
    object_b_id: str
    ground_truth_depth_a_m: float
    estimated_depth_a_m: float
    depth_a_error_m: float
    depth_a_error_pct: float
    ground_truth_depth_b_m: float
    estimated_depth_b_m: float
    depth_b_error_m: float
    depth_b_error_pct: float
    ground_truth_distance_3d_m: float
    estimated_distance_3d_m: float
    distance_3d_error_m: float
    distance_3d_error_pct: float
    tolerance_pct: float
    within_tolerance: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "object_a_id": self.object_a_id,
            "object_b_id": self.object_b_id,
            "ground_truth_depth_a_m": self.ground_truth_depth_a_m,
            "estimated_depth_a_m": self.estimated_depth_a_m,
            "depth_a_error_m": self.depth_a_error_m,
            "depth_a_error_pct": self.depth_a_error_pct,
            "ground_truth_depth_b_m": self.ground_truth_depth_b_m,
            "estimated_depth_b_m": self.estimated_depth_b_m,
            "depth_b_error_m": self.depth_b_error_m,
            "depth_b_error_pct": self.depth_b_error_pct,
            "ground_truth_distance_3d_m": self.ground_truth_distance_3d_m,
            "estimated_distance_3d_m": self.estimated_distance_3d_m,
            "distance_3d_error_m": self.distance_3d_error_m,
            "distance_3d_error_pct": self.distance_3d_error_pct,
            "tolerance_pct": self.tolerance_pct,
            "within_tolerance": self.within_tolerance,
        }


def evaluate_distance(
    predicted_result: Dict[str, Any],
    ground_truth_pair: Any,
    obj_a_gt: Optional[Any] = None,
    obj_b_gt: Optional[Any] = None,
    tolerance_pct: Optional[float] = None
) -> DistanceEvaluationResult:
    """Verify calculated 3D distance against mathematically bounded ground truth."""
    pair_id = getattr(ground_truth_pair, "pair_id", "pair_eval")
    a_id = getattr(ground_truth_pair, "object_a_id", "obj_a")
    b_id = getattr(ground_truth_pair, "object_b_id", "obj_b")

    gt_d3d = float(getattr(ground_truth_pair, "ground_truth_distance_3d_m", 0.0))
    tol = tolerance_pct if tolerance_pct is not None else float(getattr(ground_truth_pair, "tolerance_pct", 5.0))

    gt_za = float(getattr(obj_a_gt, "depth_z_m", 0.0)) if obj_a_gt else 0.0
    gt_zb = float(getattr(obj_b_gt, "depth_z_m", 0.0)) if obj_b_gt else 0.0

    # Extract estimates from service result
    est_za = float(predicted_result.get("depth_object_a") or predicted_result.get("object_a", {}).get("estimated_depth_z") or 0.0)
    est_zb = float(predicted_result.get("depth_object_b") or predicted_result.get("object_b", {}).get("estimated_depth_z") or 0.0)
    est_d3d = float(
        predicted_result.get("distance_3d_meters")
        or predicted_result.get("metrics", {}).get("estimated_relative_distance_m")
        or 0.0
    )

    err_za = round(abs(est_za - gt_za), 4)
    pct_za = round((err_za / gt_za * 100.0), 2) if gt_za > 0 else 0.0

    err_zb = round(abs(est_zb - gt_zb), 4)
    pct_zb = round((err_zb / gt_zb * 100.0), 2) if gt_zb > 0 else 0.0

    err_d3d = round(abs(est_d3d - gt_d3d), 4)
    pct_d3d = round((err_d3d / gt_d3d * 100.0), 2) if gt_d3d > 0 else 0.0

    within_tol = pct_d3d <= tol

    return DistanceEvaluationResult(
        pair_id=pair_id,
        object_a_id=a_id,
        object_b_id=b_id,
        ground_truth_depth_a_m=round(gt_za, 2),
        estimated_depth_a_m=round(est_za, 2),
        depth_a_error_m=err_za,
        depth_a_error_pct=pct_za,
        ground_truth_depth_b_m=round(gt_zb, 2),
        estimated_depth_b_m=round(est_zb, 2),
        depth_b_error_m=err_zb,
        depth_b_error_pct=pct_zb,
        ground_truth_distance_3d_m=round(gt_d3d, 2),
        estimated_distance_3d_m=round(est_d3d, 2),
        distance_3d_error_m=err_d3d,
        distance_3d_error_pct=pct_d3d,
        tolerance_pct=tol,
        within_tolerance=within_tol,
    )


def measure_latency(
    inference_fn: Callable[[], Any],
    runs: int = 5,
    warmup: int = 2
) -> Dict[str, float]:
    """Measure inference latency using high-resolution performance timers."""
    for _ in range(warmup):
        try:
            inference_fn()
        except Exception:
            pass

    times_ms = []
    for _ in range(max(1, runs)):
        t0 = time.perf_counter()
        inference_fn()
        t1 = time.perf_counter()
        times_ms.append((t1 - t0) * 1000.0)

    times_sorted = sorted(times_ms)
    mean_val = sum(times_ms) / len(times_ms)
    min_val = times_sorted[0]
    max_val = times_sorted[-1]
    p50_idx = int(len(times_sorted) * 0.50)
    p95_idx = min(len(times_sorted) - 1, int(len(times_sorted) * 0.95))
    p50_val = times_sorted[p50_idx]
    p95_val = times_sorted[p95_idx]

    return {
        "mean_ms": round(mean_val, 2),
        "min_ms": round(min_val, 2),
        "max_ms": round(max_val, 2),
        "p50_ms": round(p50_val, 2),
        "p95_ms": round(p95_val, 2),
        "runs": len(times_ms),
    }


@dataclass
class BenchmarkSummary:
    """Consolidated benchmark summary aggregator across all scenes."""
    total_scenes: int = 0
    total_ground_truth_objects: int = 0
    total_predictions: int = 0
    mean_inference_time_ms: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    map50: float = 0.0
    mean_iou: float = 0.0
    total_distance_pairs_tested: int = 0
    passed_distance_pairs: int = 0
    mean_distance_error_m: float = 0.0
    mean_distance_error_pct: float = 0.0
    max_distance_error_pct: float = 0.0
    distance_tolerance_pass_rate_pct: float = 100.0
    all_tolerances_passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_scenes": self.total_scenes,
            "total_ground_truth_objects": self.total_ground_truth_objects,
            "total_predictions": self.total_predictions,
            "mean_inference_time_ms": self.mean_inference_time_ms,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "map50": self.map50,
            "mean_iou": self.mean_iou,
            "total_distance_pairs_tested": self.total_distance_pairs_tested,
            "passed_distance_pairs": self.passed_distance_pairs,
            "mean_distance_error_m": self.mean_distance_error_m,
            "mean_distance_error_pct": self.mean_distance_error_pct,
            "max_distance_error_pct": self.max_distance_error_pct,
            "distance_tolerance_pass_rate_pct": self.distance_tolerance_pass_rate_pct,
            "status": "PASSED" if self.all_tolerances_passed else "FAILED",
        }
