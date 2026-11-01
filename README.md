# YOLO Object Detection & Monocular 3D Distance Measurement System

A comprehensive, production-ready computer vision platform combining **Ultralytics YOLOv8 nano** object detection with an analytical **monocular pinhole 3D projective distance estimation engine**. The system includes a high-performance Flask WSGI backend, a modern Vite React SPA frontend, an automated accuracy benchmark suite, a 50-client asynchronous stress testing pipeline, a 68-test 4-tier E2E test harness, and containerized Docker orchestration with automated healthchecks.

---

## 1. System Architecture

```
                                SYSTEM ARCHITECTURE OVERVIEW
                                
   +----------------------------------------------------------------------------------+
   |                                 CLIENT BROWSERS                                  |
   |              (Interactive Web UI / REST API Clients / Benchmark CLI)             |
   +-----------------------------------------+----------------------------------------+
                                             | HTTP / Port 3000 (UI) & Port 5000 (API)
                                             v
   +----------------------------------------------------------------------------------+
   |                        DOCKER CONTAINER ORCHESTRATION                            |
   |                                                                                  |
   |  +-------------------------------------+  +-----------------------------------+  |
   |  |   Frontend Container (Nginx Alpine) |  |   Backend Container (Python 3.11) |  |
   |  |   - React 19 + Vite 8 + Tailwind 4  |  |   - Production Flask 3.1 WSGI     |  |
   |  |   - SPA Client & Canvas Rendering   |  |   - Gunicorn (4 workers, 2 thr)   |  |
   |  |   - Reverse Proxy (/api/ -> Backend)|  |   - OpenCV Headless (cv2)         |  |
   |  |   - Healthcheck: GET /health        |  |   - Ultralytics YOLOv8n (cached)  |  |
   |  |   - Port: 3000 (maps to Nginx 80)   |  |   - Healthcheck: GET /api/health  |  |
   |  +------------------+------------------+  +-----------------+-----------------+  |
   |                     |                                       |                    |
   |                     +-------------------+-------------------+                    |
   |                                         | Internal Bridge Network                |
   |                                         v                                        |
   |                     +---------------------------------------+                    |
   |                     |    Core Computer Vision Pipelines     |                    |
   |                     |  - YOLOv8 Object Detector             |                    |
   |                     |  - Pinhole Projective Depth Engine    |                    |
   |                     |  - 3D Metric Coordinate Projector     |                    |
   |                     |  - Relative 3D Euclidean Separator    |                    |
   |                     +---------------------------------------+                    |
   +----------------------------------------------------------------------------------+
```

### Component Breakdown
1. **Computer Vision Backend (`backend/`)**:
   - **Framework**: Flask 3.1 with production WSGI support (Gunicorn in Linux containers, Waitress / Werkzeug multi-threaded locally).
   - **Object Detection Service (`yolo_detector.py`)**: Ultralytics YOLOv8 nano model (`yolov8n.pt`) with offline path caching to eliminate runtime model downloads.
   - **Distance Estimator Engine (`distance_estimator.py`)**: Pinhole optical depth calculation, class-specific physical height priors (car, person, forklift, bus, truck, etc.), 3D camera coordinate projection, and Euclidean separation.
   - **Defensive API Layer (`routes/api.py`)**: Comprehensive validation rejecting corrupt Base64, 0-byte images, missing parameters, and negative coordinates with deterministic HTTP 400 errors (zero 500 crashes).
2. **Web Frontend (`frontend/`)**:
   - **Framework**: React 19, Vite 8, Tailwind CSS 4.
   - **User Experience**: Interactive image upload, canvas bounding box visualization, object pair selection, real-time depth inspection, and 3D Euclidean distance overlay.
   - **Web Server**: Multi-stage Nginx container serving static production assets and reverse-proxying `/api/` traffic to the backend.
3. **Automated Benchmark Suite (`benchmarks/`)**:
   - 4 calibrated reference scenes (Urban Traffic, Warehouse Logistics, Calibrated Optical Bench, Pedestrian Crosswalk).
   - Ground truth metrics (IoU, Precision, Recall, mAP50, Inference Latency, 3D Euclidean Distance Error $< 5\%$ standard, $< 0.5\%$ optical).
4. **Stress Testing Pipeline (`stress_testing/`)**:
   - 50 concurrent virtual clients, P50-P99 latency distribution profiling, `psutil` real-time RSS memory leak tracking, and CPU hardware bottleneck attribution.
5. **E2E & Integration Test Suites (`e2e_tests/` & `tests/`)**:
   - 68-test 4-tier opaque-box E2E test harness covering features, boundaries, cross-feature combinations, and real-world workloads.
   - Comprehensive unit and integration test suite covering detector, geometry, and utility modules.

---

## 2. Monocular Distance Estimation Geometry

Physical 3D measurements are mathematically computed from monocular 2D images using analytical pinhole projective geometry.

### 2.1 Monocular Projective Depth ($Z$)
The projective depth of a detected object along the optical $Z$-axis is:

$$Z = \frac{f \cdot H_{real}}{h_{pixels}}$$

Where:
- $f$: Camera focal length in pixels (defaults to $0.9 \cdot \text{image\_width}$ when uncalibrated, or calibrated intrinsic $f_x$).
- $H_{real}$: Physical height of the object class in meters, retrieved from calibrated priors:
  * `car`: $1.50\text{m}$
  * `person`: $1.70\text{m}$
  * `forklift`: $2.20\text{m}$
  * `bus`: $3.20\text{m}$
  * `truck`: $2.80\text{m}$
  * `motorcycle` / `bicycle`: $1.10\text{m}$
  * Default fallback: $1.50\text{m}$
- $h_{pixels}$: Bounding box pixel height ($y_2 - y_1$), clamped to $\max(1.0, h)$ to prevent division by zero.

### 2.2 Camera Space 3D Coordinate Projection ($X, Y, Z$)
Given the optical principal point $(c_x, c_y) = \left(\frac{W}{2}, \frac{H}{2}\right)$ and detected 2D center $(cx, cy)$:

$$X = \frac{(cx - c_x) \cdot Z}{f}$$

$$Y = \frac{(cy - c_y) \cdot Z}{f}$$

This yields metric camera space coordinates $(X, Y, Z)$ in meters.

### 2.3 3D Euclidean Spatial Separation ($D_{3D}$)
The metric spatial separation between two detected objects $A$ and $B$ is:

$$D_{3D} = \sqrt{\Delta X^2 + \Delta Y^2 + \Delta Z^2} = \sqrt{(X_B - X_A)^2 + (Y_B - Y_A)^2 + (Z_B - Z_A)^2}$$

### 2.4 Scale-Invariant Normalized Metrics
- **2D Pixel Distance**:
  $$D_{pixel} = \sqrt{(cx_B - cx_A)^2 + (cy_B - cy_A)^2}$$
- **Normalized Image Diagonal Percentage**:
  $$\text{Norm} \% = \left(\frac{D_{pixel}}{\sqrt{W^2 + H^2}}\right) \times 100\%$$

---

## 3. Quick Start & CLI Reproduction Commands

All test suites, benchmarks, stress tests, and deployment commands are fully reproducible via standard CLI commands:

### 3.1 Run Accuracy Benchmarks
Executes the automated benchmark suite across all 4 calibrated reference scenes, validates mathematically bounded error tolerances ($<5\%$ standard, $<0.5\%$ optical), and outputs structured `benchmark_results.json`:
```bash
python benchmarks/run_benchmarks.py
```

### 3.2 Run Concurrency & Latency Stress Tests
Simulates 50 concurrent virtual clients targeting detection and distance endpoints, profiles P50-P99 latency percentiles, tracks RSS memory leaks via `psutil`, documents hardware bottlenecks, and outputs `stress_test_report.json`:
```bash
python stress_testing/run_stress_test.py --clients 50 --requests 100
```

### 3.3 Run Unit & Integration Tests
Runs the full suite of 102 unit and API integration tests:
```bash
python -m pytest tests/ -v
```
*Alternatively, run the standalone test runner:*
```bash
python tests/run_tests.py
```

### 3.4 Run 4-Tier End-to-End (E2E) Test Suite
Runs the 68-test opaque-box E2E test harness covering Feature Coverage (Tier 1), Boundary Cases (Tier 2), Cross-Feature Combinations (Tier 3), and Real-World Workloads (Tier 4):
```bash
python -m pytest e2e_tests/ -v
```
*Alternatively, run the standalone E2E CLI runner:*
```bash
python e2e_tests/run_e2e_suite.py --all
```

### 3.5 Containerized Production Deployment (Docker Compose)
Build and spin up the multi-service containerized environment (Flask backend + Vite React frontend + Nginx):
```bash
# Build production images cleanly with zero build errors
docker compose build

# Launch services in detached mode
docker compose up -d
```

### 3.6 Automated Healthcheck Verification
Verify service availability and health status across backend and frontend containers:
```bash
# Verify Backend Health (Port 5000)
curl -f http://localhost:5000/api/health

# Verify Frontend / Nginx Gateway Health (Port 3000)
curl -f http://localhost:3000/health
```

---

## 4. REST API Specification

### 4.1 Health Check (`GET /api/health`)
- **Request**: `GET /api/health`
- **Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "service": "YOLO Object Detection & Distance Estimation API",
    "yolo_loaded": true,
    "model_name": "yolov8n.pt",
    "load_error": null,
    "domain": "Computer Vision & Spatial Analytics"
  }
  ```

### 4.2 Object Detection (`POST /api/detect`)
- **Supported Encodings**:
  * Multipart form-data (`image` file: `.jpg`, `.png`, `.webp`)
  * JSON Base64 data URL (`{"image_base64": "data:image/jpeg;base64,..."}`)
  * JSON raw Base64 string (`{"image_base64": "/9j/4AAQ..."}`)
- **Optional Parameters**: `conf` (0.0 - 1.0, default 0.25), `iou` (0.0 - 1.0, default 0.45).
- **Response (200 OK)**:
  ```json
  {
    "model_used": "yolov8n.pt",
    "inference_time_ms": 35.2,
    "image_dimensions": {"width": 960, "height": 600},
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
    "original_image": "data:image/jpeg;base64,...",
    "annotated_image": "data:image/jpeg;base64,..."
  }
  ```

### 4.3 3D Distance Calculation (`POST /api/distance`)
- **Request (JSON)**:
  ```json
  {
    "object_a": {
      "class": "car",
      "height": 140,
      "center": [270.0, 430.0],
      "bbox": [140, 360, 400, 500]
    },
    "object_b": {
      "class": "car",
      "height": 110,
      "center": [685.0, 365.0],
      "bbox": [580, 310, 790, 420]
    },
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
    "camera_coords_a": {"x": -2.25, "y": 1.39, "z": 9.26},
    "camera_coords_b": {"x": 2.79, "y": 0.89, "z": 11.78},
    "visualization_image": "data:image/jpeg;base64,..."
  }
  ```

---

## 5. Project Directory Structure

```
yolo-object-distance-system/
├── backend/                             # Python Computer Vision Backend
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py                      # REST endpoints (/api/detect, /api/distance, /api/health)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── distance_estimator.py       # Pinhole 3D distance engine & class priors
│   │   └── yolo_detector.py            # Ultralytics YOLOv8n detector service
│   ├── utils/
│   │   ├── __init__.py
│   │   └── image_utils.py              # Base64, multipart, and OpenCV transforms
│   ├── app.py                          # Flask application factory
│   ├── config.py                       # Configuration & absolute model paths
│   ├── Dockerfile                      # Production Python 3.11-slim container
│   └── wsgi.py                         # Waitress/Werkzeug/Gunicorn WSGI launcher
├── frontend/                            # React 19 + Vite 8 SPA Client
│   ├── src/
│   │   ├── components/                 # Canvas, ImageUploader, DistanceCard, Controls
│   │   ├── App.jsx                     # Interactive UI state machine
│   │   └── main.jsx                    # Application entry point
│   ├── Dockerfile                      # Multi-stage Node 20 builder -> Nginx Alpine
│   ├── nginx.conf                      # Nginx reverse proxy & /health endpoint
│   ├── package.json
│   └── vite.config.js
├── benchmarks/                          # Automated Accuracy Benchmark Suite (R1)
│   ├── calibrated_scenes.py            # 4 programmatic calibrated reference scenes
│   ├── evaluators.py                   # IoU, mAP, precision/recall, 3D distance metrics
│   ├── reference_data/                 # Generated calibrated scene images (.jpg)
│   └── run_benchmarks.py               # Standalone CLI benchmark runner
├── stress_testing/                      # Concurrency & Latency Stress Pipeline (R2)
│   ├── concurrent_runner.py            # 50-client async load generator
│   ├── latency_profiler.py             # P50-P99 distribution & CPU bottleneck profiler
│   ├── memory_tracker.py               # Real-time RSS memory leak tracker (psutil)
│   └── run_stress_test.py              # Standalone CLI stress test runner
├── tests/                               # Unit & API Integration Tests (R3)
│   ├── conftest.py                     # Pytest fixtures & synthetic test images
│   ├── test_unit_detector.py           # YOLO detector unit tests
│   ├── test_unit_distance.py           # Pinhole geometry math unit tests
│   ├── test_unit_image_utils.py        # Image format & decoding tests
│   ├── test_api_endpoints.py           # REST API schema & status code tests
│   └── test_edge_cases.py              # Corrupt base64, 0-byte, 0-height edge cases
├── e2e_tests/                           # 4-Tier Opaque-Box E2E Test Suite
│   ├── conftest.py                     # In-memory WSGI fixtures & scene generators
│   ├── test_tier1_features.py          # Tier 1: Feature Coverage (29 tests)
│   ├── test_tier2_boundaries.py        # Tier 2: Boundary & Corner Cases (23 tests)
│   ├── test_tier3_combinations.py      # Tier 3: Cross-Feature Combinations (10 tests)
│   ├── test_tier4_workloads.py         # Tier 4: Real-World Workloads (6 tests)
│   └── run_e2e_suite.py                # Standalone E2E CLI test runner
├── benchmark_results.json               # Structured accuracy benchmark output
├── stress_test_report.json              # Structured concurrency stress test report
├── BENCHMARK_GUIDE.md                   # Comprehensive benchmark & stress testing manual
├── TEST_INFRA.md                        # E2E test infrastructure specification
├── TEST_READY.md                        # E2E test execution & verification checklist
├── docker-compose.yml                   # Multi-service production orchestration
├── pyproject.toml                       # Python package configuration
├── requirements.txt                     # Production dependencies
├── requirements-dev.txt                 # Development & test dependencies
├── yolov8n.pt                           # Pre-trained YOLOv8 nano model weights
└── README.md                            # Primary project documentation
```

---

## 6. Verified Performance & Quality Summary

### 6.1 Accuracy Benchmark Scorecard (`benchmark_results.json`)

| Benchmark Scene | Resolution | Target A Depth | Target B Depth | GT Distance | Estimated | Error (%) | Tolerance | Result |
|-----------------|:----------:|:--------------:|:--------------:|:-----------:|:---------:|:---------:|:---------:|:------:|
| **Urban Traffic** | $960 \times 600$ | $9.26\text{m}$ | $11.78\text{m}$ | $5.66\text{m}$ | $5.66\text{m}$ | $0.08\%$ | $< 5.0\%$ | **PASS** |
| **Warehouse Logistics** | $1280 \times 720$ | $9.20\text{m}$ | $5.59\text{m}$ | $4.60\text{m}$ | $4.60\text{m}$ | $0.10\%$ | $< 5.0\%$ | **PASS** |
| **Optical Bench** | $1000 \times 800$ | $7.50\text{m}$ | $15.00\text{m}$ | $7.73\text{m}$ | $7.73\text{m}$ | **$0.01\%$** | **$< 0.5\%$** | **PASS** |
| **Pedestrian Crosswalk** | $1000 \times 800$ | $8.00\text{m}$ | $8.00\text{m}$ | $4.00\text{m}$ | $4.00\text{m}$ | **$0.00\%$** | $< 5.0\%$ | **PASS** |

- **Mean 3D Distance Error**: $0.0024\text{m}$ ($0.05\%$)
- **Mean Single-Frame Inference Latency**: $65.86\text{ms}$
- **Overall Tolerance Pass Rate**: $100.0\%$ ($4 / 4$ scenes compliant)

### 6.2 Concurrency Stress Test Scorecard (`stress_test_report.json`)

| Metric | Target Specification | Empirical Result | Status |
|--------|:--------------------:|:----------------:|:------:|
| **Concurrent Virtual Clients** | $\ge 50$ clients | $50$ concurrent clients | **PASS** |
| **Total Executed Requests** | $\ge 100$ requests | $100$ requests | **PASS** |
| **Unhandled HTTP 5xx Errors** | $0.0\%$ | **$0.0\%$ (0 errors)** | **PASS** |
| **Request Success Rate** | $100\%$ | **$100.0\%$ (100 / 100)** | **PASS** |
| **Distance API P50 Latency** | $< 500\text{ms}$ | **$324.2\text{ms}$** | **PASS** |
| **Memory Leak Detection** | $\Delta \text{RSS} < 50\text{MB}$ | $+15.0\text{MB}$ (Stable) | **PASS** |
| **Hardware Bottleneck Attribution** | Formally documented | CPU-bound ($98.1\%$ inference) | **PASS** |

### 6.3 4-Tier E2E Test Suite Scorecard (`TEST_READY.md`)

| Tier | Test Suite File | Focus Area | Executed | Passed | Pass Rate |
|------|-----------------|------------|:--------:|:------:|:---------:|
| **Tier 1** | `test_tier1_features.py` | Feature Coverage (Root, Health, Detect, Distance, CORS) | 29 | 29 | **100%** |
| **Tier 2** | `test_tier2_boundaries.py` | Boundary & Corner Cases (0-byte, corrupt headers, div-by-zero) | 23 | 23 | **100%** |
| **Tier 3** | `test_tier3_combinations.py` | Cross-Feature Interactions (5 formats, focal scaling, symmetry) | 10 | 10 | **100%** |
| **Tier 4** | `test_tier4_workloads.py` | Real-World Workloads (Traffic, Forklift, Optical Bench $<0.5\%$) | 6 | 6 | **100%** |
| **TOTAL** | `e2e_tests/` | **Complete E2E Opaque-Box Suite** | **68** | **68** | **100%** |

---

## 7. License & Credits

Built as part of the **YOLO Object Distance System Engineering Project**.
- Object Detection powered by [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics).
- Computer Vision and image transformations powered by [OpenCV](https://opencv.org/).
- Web UI built with [React](https://react.dev/), [Vite](https://vitejs.dev/), and [Tailwind CSS](https://tailwindcss.com/).
