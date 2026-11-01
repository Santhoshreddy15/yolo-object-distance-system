# Project: YOLO Object Detection & Distance Measurement System

## Architecture
The system consists of:
1. **Computer Vision Backend (Flask + PyTorch / Ultralytics YOLOv8n)**:
   - REST API serving object detection, camera calibration, and monocular 3D distance estimation.
   - Pinhole camera projective depth estimation: $Z = \frac{f \cdot H_{real}}{h_{pixels}}$.
   - 3D camera coordinate projection: $X = \frac{(cx - c_x) \cdot Z}{f}$, $Y = \frac{(cy - c_y) \cdot Z}{f}$.
   - Relative 3D Euclidean separation: $D_{3D} = \sqrt{\Delta X^2 + \Delta Y^2 + \Delta Z^2}$.
   - Production WSGI runtime (Waitress / Gunicorn).
2. **Web Frontend (React 19 + Vite 8 + Tailwind CSS 4)**:
   - Interactive client with real-time detection display and interactive 3D distance measurement between pair-selected objects.
3. **Automated Evaluation & Accuracy Benchmark Suite (R1)**:
   - Calibrated reference scene evaluation and synthetic/photographic test scenes.
   - Ground truth metrics: Precision, Recall, IoU, Mean Inference Latency, Relative 3D Distance Error.
   - Single-command CLI runner outputting `benchmark_results.json` and formatted report.
4. **Concurrency & Latency Stress Testing Pipeline (R2)**:
   - Asynchronous load generator running 50+ concurrent virtual clients.
   - Latency distribution profiler (P50, P90, P95, P99).
   - Sustained run memory leak detection via `psutil`.
   - Hardware bottleneck attribution logging for CPU inference.
5. **Integration & Edge-Case Test Suite (R3)**:
   - Comprehensive Pytest suite covering all image formats (JPEG, PNG, WEBP, raw Base64, Data URL Base64, multipart).
   - Edge case validation: 0 objects, 1 object, corrupted payloads, 0-byte images, missing calibration, extreme aspect ratios.
   - Zero 500 crashes; deterministic 400 Bad Request error codes.
6. **Containerized Production Deployment (R4)**:
   - Multi-stage frontend Dockerfile with Nginx reverse proxy.
   - Backend Dockerfile with Python 3.11-slim, OpenCV headless, local model caching, and healthcheck probe.
   - `docker-compose.yml` service orchestration.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Dependencies & Package Management | Create `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` | M0 (Foundational) | Survey |
| F2 | Model Offline Path Caching | Ensure `config.py` resolves `yolov8n.pt` absolutely to prevent re-downloads | M0 (Foundational) | Survey |
| F3 | API Defensive Error Hardening | Fix unhandled exceptions in `api.py` (corrupted base64, empty images, malformed JSON -> 400) | M0 (Foundational) | Survey |
| F4 | Forklift Class Prior Support | Add `forklift: 2.20` to `CLASS_REFERENCE_HEIGHTS` in `distance_estimator.py` | M0 (Foundational) | Survey |
| F5 | Calibrated Reference Scene Dataset | Ground truth 3D locations, bounding boxes, and camera parameters for benchmark evaluation | M1 (R1 Benchmark) | ORIGINAL_REQUEST R1 |
| F6 | Precision, Recall & IoU Evaluator | Object detection accuracy evaluation against labeled reference targets | M1 (R1 Benchmark) | ORIGINAL_REQUEST R1 |
| F7 | Monocular 3D Distance Error Evaluator | Calculates relative distance error against analytical ground truth with bounded tolerances | M1 (R1 Benchmark) | ORIGINAL_REQUEST R1 |
| F8 | Single-CLI Benchmark Runner | Executes evaluation suite and outputs structured `benchmark_results.json` + summary report | M1 (R1 Benchmark) | ORIGINAL_REQUEST R1 |
| F9 | High-Concurrency Load Generator | Asynchronous client generating 50+ simultaneous requests to `/api/detect` and `/api/distance` | M2 (R2 Stress) | ORIGINAL_REQUEST R2 |
| F10 | Latency Percentile Profiler | Measures P50, P90, P95, P99 latency percentiles; enforces P95 < 80ms or logs CPU bottleneck | M2 (R2 Stress) | ORIGINAL_REQUEST R2 |
| F11 | Memory Leak Profiler | Monitors RSS memory utilization over sustained test load using `psutil` | M2 (R2 Stress) | ORIGINAL_REQUEST R2 |
| F12 | Multi-Threaded WSGI Server | Configure production WSGI runner (Waitress/Gunicorn) to ensure 0% 5xx under 50+ concurrent clients | M2 (R2 Stress) | ORIGINAL_REQUEST R2 |
| F13 | Image Ingestion Format Tests | Pytest tests for JPEG, PNG, WEBP, Data URL Base64, raw Base64, and multipart form-data | M3 (R3 Integration) | ORIGINAL_REQUEST R3 |
| F14 | Edge-Case Robustness Tests | Pytest tests for 0 objects, 1 object, corrupted image, 0-byte file, missing calibration, extreme aspect ratios | M3 (R3 Integration) | ORIGINAL_REQUEST R3 |
| F15 | API Schema & Status Code Tests | Complete test verification of `/`, `/api/health`, `/api/detect`, `/api/distance` with 100% pass rate | M3 (R3 Integration) | ORIGINAL_REQUEST R3 |
| F16 | Multi-Stage Frontend Dockerfile | Node 20 builder to Nginx server with `/api/` reverse proxy and healthcheck | M4 (R4 Container) | ORIGINAL_REQUEST R4 |
| F17 | Production Backend Dockerfile | Python 3.11-slim, OpenCV headless, baked-in model caching, healthcheck probe | M4 (R4 Container) | ORIGINAL_REQUEST R4 |
| F18 | Docker Compose Orchestration | Multi-service composition linking frontend and backend with automated healthchecks | M4 (R4 Container) | ORIGINAL_REQUEST R4 |
| F19 | Opaque-Box E2E Test Suite (Tiers 1-4) | Requirement-driven test suite with 4 tiers (Feature, Boundary, Combinatorial, Workload) | E2E Testing Track | Dual Track |
| F20 | Adversarial Coverage Hardening (Tier 5) | White-box stress tests, extreme permutations, and edge coverage validation | Final Milestone | Dual Track |
| F21 | CLI Reproduction Documentation | Complete reproduction guide with copy-pasteable commands in `README.md` and `BENCHMARK_GUIDE.md` | M5 (Documentation) | Acceptance Criteria |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Foundational Hardening | F1, F2, F3, F4 (Dependencies, model caching, defensive error handling, class priors) | none | DONE |
| M1 | Automated Evaluation & Accuracy Benchmark Suite (R1) | F5, F6, F7, F8 (Calibrated dataset, IoU/mAP, 3D distance error, `benchmark_results.json`) | M0 | DONE |
| M2 | Concurrency & Latency Stress Testing Pipeline (R2) | F9, F10, F11, F12 (50+ clients, P50-P99 latency, memory leak detector, WSGI runner) | M0 | DONE |
| M3 | Integration & Edge-Case Test Suite (R3) | F13, F14, F15 (Image formats, edge cases, 100% pass rate) | M0 | DONE |
| M4 | Containerized Production Deployment (R4) | F16, F17, F18 (Dockerfiles, compose, healthchecks, offline model) | M0 | DONE |
| E2E | Opaque-Box E2E Testing Track | F19 (Tiers 1-4 requirement-driven opaque-box test harness, `TEST_READY.md`) | none | DONE |
| M5 | Final Acceptance & Documentation | F20, F21 (100% E2E pass, Tier 5 adversarial testing, `BENCHMARK_GUIDE.md`, `README.md`) | M1, M2, M3, M4, E2E | DONE |

---

## Interface Contracts
### `POST /api/detect`
- **Request (Multipart)**: `image` (file: .jpg, .jpeg, .png, .webp), optional `conf` (float, 0.0-1.0), optional `iou` (float, 0.0-1.0)
- **Request (JSON)**: `{"image_base64": "<data_url or raw_base64>", "conf": 0.25, "iou": 0.45}`
- **Response (200 OK)**:
  ```json
  {
    "count": 2,
    "detections": [
      {
        "id": 1,
        "class": "car",
        "confidence": 0.88,
        "bbox": [140, 360, 400, 500],
        "width": 260,
        "height": 140,
        "center": [270.0, 430.0],
        "bottom_center": [270.0, 500.0]
      }
    ],
    "inference_time_ms": 35.2,
    "image_width": 960,
    "image_height": 600,
    "image_base64": "data:image/jpeg;base64,..."
  }
  ```
- **Error (400 Bad Request)**: `{"error": "<descriptive message>"}` for missing image, corrupted base64, 0-byte file, invalid numeric range.
- **Error (413 Payload Too Large)**: For images > 16MB.

### `POST /api/distance`
- **Request (JSON)**:
  ```json
  {
    "object_a": {"class": "car", "height": 140, "center": [270, 430], "bbox": [140, 360, 400, 500]},
    "object_b": {"class": "car", "height": 110, "center": [685, 365], "bbox": [580, 310, 790, 420]},
    "image_dimensions": {"width": 960, "height": 600},
    "focal_length_px": 864.0
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "depth_object_a": 9.26,
    "depth_object_b": 11.78,
    "distance_3d_meters": 5.66,
    "pixel_distance": 420.1,
    "normalized_distance_pct": 37.1,
    "focal_length_px": 864.0,
    "object_a": {...},
    "object_b": {...}
  }
  ```
- **Error (400 Bad Request)**: Missing object_a/object_b, invalid JSON, missing dimensions when needed.

---

## Code Layout
```
yolo-object-distance-system/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── distance_estimator.py
│   │   └── yolo_detector.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── image_utils.py
│   ├── Dockerfile
│   └── wsgi.py
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── benchmarks/
│   ├── __init__.py
│   ├── calibrated_scenes.py
│   ├── evaluators.py
│   ├── reference_data/
│   └── run_benchmarks.py
├── stress_testing/
│   ├── __init__.py
│   ├── concurrent_runner.py
│   ├── latency_profiler.py
│   ├── memory_tracker.py
│   └── run_stress_test.py
├── tests/
│   ├── conftest.py
│   ├── test_unit_detector.py
│   ├── test_unit_distance.py
│   ├── test_unit_image_utils.py
│   ├── test_api_endpoints.py
│   └── test_edge_cases.py
├── e2e_tests/
│   ├── test_tier1_features.py
│   ├── test_tier2_boundaries.py
│   ├── test_tier3_combinations.py
│   ├── test_tier4_workloads.py
│   └── run_e2e_suite.py
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── benchmark_results.json
├── BENCHMARK_GUIDE.md
└── README.md
```
