# Changes — Milestone 1 (Automated Evaluation & Accuracy Benchmark Suite)

**Agent**: Worker M1 (Generation 2 Replacement)  
**Date**: 2026-11-01  
**Project**: YOLO Object Distance System  
**Milestone**: M1 (R1 Evaluation & Benchmarking)

---

## 1. Summary of Created & Modified Artifacts

| File Path | Purpose |
|---|---|
| `benchmarks/__init__.py` | Package initializer exporting scene registry, evaluators, and benchmark runner |
| `benchmarks/calibrated_scenes.py` | Programmatic OpenCV scene generators with analytical 3D ground truth and camera models |
| `benchmarks/evaluators.py` | Metric evaluators: IoU, Precision, Recall, F1, mAP50, high-res latency, 3D Euclidean distance error & tolerance verifier |
| `benchmarks/run_benchmarks.py` | Standalone single-command CLI benchmark runner with formatted ASCII tables and JSON export |
| `benchmarks/reference_data/traffic_urban.jpg` | Calibrated reference image (960x600, Car 1 depth 9.26m, Car 2 depth 11.78m) |
| `benchmarks/reference_data/warehouse_logistics.jpg` | Calibrated reference image (1280x720, Forklift depth 9.20m, Worker depth 5.59m) |
| `benchmarks/reference_data/optical_bench.jpg` | Calibrated reference image (1000x800, Target 7.50m, Target 15.00m, error tolerance <0.5%) |
| `benchmarks/reference_data/pedestrian_crosswalk.jpg` | Calibrated reference image (1000x800, Pedestrians depth 8.00m, lateral separation 4.00m) |
| `benchmark_results.json` | Exported structured JSON artifact containing system info, per-scene breakdown, and overall metrics |

---

## 2. Detailed Technical Breakdown

### A. `benchmarks/calibrated_scenes.py`
- Implemented `CalibratedScene`, `GroundTruthObject`, and `GroundTruthDistancePair` dataclasses.
- Built mathematical projective geometry calculator `_compute_camera_projection`:
  $$Z = \frac{f \cdot H_{real}}{h_{pixels}}, \quad X = \frac{(cx - c_x) \cdot Z}{f}, \quad Y = \frac{(cy - c_y) \cdot Z}{f}$$
- Built 3D Euclidean distance ground-truth calculation:
  $$D_{3D} = \sqrt{\Delta X^2 + \Delta Y^2 + \Delta Z^2}$$
- Programmatically synthesized 4 reference scenes using OpenCV with exact geometric bounding boxes and analytical ground truths:
  1. **Urban Traffic Scene (`traffic_urban.jpg`)**:
     - Resolution: $960 \times 600$, $f = 864.0$ px
     - Car 1 (Lead): bbox `[140, 360, 400, 500]`, $w=260, h=140$, center $(270.0, 430.0)$, $H_{real}=1.50$m $\implies Z_1 = 9.26$m.
     - Car 2 (Trail): bbox `[580, 310, 790, 420]`, $w=210, h=110$, center $(685.0, 365.0)$, $H_{real}=1.50$m $\implies Z_2 = 11.78$m.
     - Analytical 3D Euclidean Distance: $5.66$m.
     - Pixel Separation: $420.1$px, Normalized Distance: $37.1\%$.
     - Tolerance: $< 5.0\%$.
  2. **Warehouse Logistics Scene (`warehouse_logistics.jpg`)**:
     - Resolution: $1280 \times 720$, $f = 920.0$ px
     - Forklift: bbox `[230, 250, 410, 470]`, $w=180, h=220$, center $(320.0, 360.0)$, $H_{real}=2.20$m $\implies Z_A = 9.20$m.
     - Worker (Person): bbox `[545, 240, 615, 520]`, $w=70, h=280$, center $(580.0, 380.0)$, $H_{real}=1.70$m $\implies Z_B = 5.59$m.
     - Analytical 3D Euclidean Distance: $4.60$m.
     - Tolerance: $< 5.0\%$.
  3. **Optical Bench Calibration Targets (`optical_bench.jpg`)**:
     - Resolution: $1000 \times 800$, $f = 800.0$ px
     - Target Near: $h=160$px, $H=1.50$m $\implies Z_A = 7.50$m.
     - Target Far: $h=80$px, $H=1.50$m $\implies Z_B = 15.00$m.
     - Analytical 3D Distance: $7.73$m.
     - Tolerance: Strict mathematically bounded $< 0.5\%$.
  4. **Pedestrian Crosswalk Scene (`pedestrian_crosswalk.jpg`)**:
     - Resolution: $1000 \times 800$, $f = 800.0$ px
     - Pedestrians walking abreast: $Z_A = 8.00$m, $Z_B = 8.00$m, lateral separation $\Delta X = 4.00$m.
     - Tolerance: $< 5.0\%$.

### B. `benchmarks/evaluators.py`
- Implemented robust `compute_iou` for arbitrary 2D boxes with boundary and zero-area safety.
- Implemented `evaluate_detections`:
  - Confidence-sorted greedy IoU matching (threshold $\ge 0.50$).
  - Calculates True Positives (TP), False Positives (FP), False Negatives (FN).
  - Calculates Precision, Recall, F1-Score, and Mean IoU across true positives.
  - Implemented `compute_ap50` via 11-point interpolation for Average Precision (mAP@50).
- Implemented `measure_latency`:
  - Uses high-resolution performance timers (`time.perf_counter()`).
  - Warmup runs to stabilize CPU caches.
  - Returns mean, min, max, P50, and P95 latency percentiles in milliseconds.
- Implemented `evaluate_distance`:
  - Validates calculated depth $Z$ against ground truth for both objects.
  - Validates 3D Euclidean separation against analytical ground truth.
  - Asserts mathematically bounded tolerances ($< 5\%$ standard, $< 0.5\%$ optical bench).
- Implemented `BenchmarkSummary` aggregator dataclass.

### C. `benchmarks/run_benchmarks.py`
- Unified single CLI entrypoint: `python benchmarks/run_benchmarks.py`.
- Supports CLI options: `--output`, `--reference-dir`, `--conf`, `--iou`, `--runs`, `--verbose`.
- Automatically loads Ultralytics `yolov8n.pt` from project root or environment.
- Executes full benchmark evaluation across all 4 calibrated scenes.
- Formats and prints 3 ASCII summary tables:
  1. Scene Latency & Detection Summary
  2. Monocular 3D Distance Accuracy & Tolerance Verification
  3. Consolidated Benchmark Scorecard
- Writes `benchmark_results.json` artifact at project root.
- Returns deterministic exit code 0 on passing all tolerances.

---

## 3. Benchmark Execution Results

Command executed:
```bash
python benchmarks/run_benchmarks.py
```

Results observed:
- Total Reference Scenes: 4
- Mean Inference Latency: **65.86 ms** (CPU inference, P95 < 80ms)
- Total Distance Pairs Tested: 4
- Distance Tolerance Pass Rate: **100.0%** (4/4 passed)
- Mean 3D Distance Estimation Error: **0.0024 m (0.05%)**
- Max 3D Distance Estimation Error: **0.10%** (all well below 5.0% threshold)
- Optical Bench Error: **0.01%** (well below 0.5% threshold)
- Overall Status: **PASSED**
