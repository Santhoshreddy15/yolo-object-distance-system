# Infrastructure, Testing & Benchmarking Survey Analysis

**Role**: Infra & Testing Explorer  
**Working Directory**: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\explorer_survey_infra`  
**Target Project**: YOLO Object Detection & Monocular Distance Estimation System  
**Date**: 2026-11-01  

---

## 1. Executive Summary

This survey provides a comprehensive audit of the infrastructure, test harness, benchmarking pipelines, dependency management, and containerization setups for the YOLO object detection and monocular distance estimation system.

### Key Takeaways
1. **Test Infrastructure**: **100% absent**. The repository contains zero test files, zero test directories (`tests/`), no test runner configurations (`pytest.ini`, `pyproject.toml`, `tox.ini`), and no frontend automated test runners.
2. **Backend Dependency Management**: **Completely missing**. No `requirements.txt`, `pyproject.toml`, or `setup.py` exists anywhere in the repository. The Flask app directly imports `flask`, `flask_cors`, `cv2`, `numpy`, `PIL`, and `ultralytics`, with no version pinning or specification.
3. **Containerization**: **Completely missing**. No `Dockerfile`, `docker-compose.yml`, `.dockerignore`, or healthcheck probes exist.
4. **Benchmarking & Stress Testing**: **Completely missing**. No performance profiling, no latency percentile collection (P50/P90/P95/P99), no 50+ concurrent virtual client stress harness, and no ground-truth accuracy benchmark suite producing `benchmark_results.json`.
5. **Core Application State**: The repository possesses functional baseline application code for Flask (`backend/app.py`, `backend/routes/api.py`, `backend/services/yolo_detector.py`, `backend/services/distance_estimator.py`) and a modern React Vite frontend (`frontend/src`). Local model weights `yolov8n.pt` (6.5 MB) exist in the project root.

---

## 2. Comprehensive Inventory of Existing Repository Assets

### 2.1 File & Directory Inventory
A complete scan of the project root (`C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system`) reveals 45 tracked files across two main tiers:

```
yolo-object-distance-system/
├── yolov8n.pt                     # 6,549,796 bytes (YOLOv8 nano PyTorch weights)
├── backend/
│   ├── app.py                     # Flask application factory, CORS, error handlers (1,417 bytes)
│   ├── config.py                  # App configuration & default thresholds (901 bytes)
│   ├── routes/
│   │   └── api.py                 # Blueprint routes: /api/health, /api/detect, /api/distance (3,741 bytes)
│   ├── services/
│   │   ├── yolo_detector.py       # YOLODetectorService wrapping Ultralytics YOLO (6,565 bytes)
│   │   └── distance_estimator.py  # DistanceEstimatorService monocular projection (7,052 bytes)
│   ├── utils/
│   │   ├── image_utils.py         # Image decoding, validation, base64 conversions (2,782 bytes)
│   │   └── sample_data.py         # Project metadata dictionary (261 bytes)
│   ├── sample_images/
│   │   └── traffic_urban.jpg      # Sample street scene image (34,960 bytes)
│   └── uploads/                   # Runtime upload directory
└── frontend/
    ├── package.json               # Vite, React 19, Tailwind CSS v4, Lucide React (553 bytes)
    ├── package-lock.json          # Node dependency lockfile (62,669 bytes)
    ├── vite.config.js             # Vite configuration with React and Tailwind plugins (279 bytes)
    ├── index.html                 # Frontend HTML template (360 bytes)
    ├── .oxlintrc.json             # Oxlint configuration (231 bytes)
    ├── README.md                  # Frontend setup guide (1,009 bytes)
    ├── public/                    # Icons and static public assets
    └── src/
        ├── App.jsx / App.css
        ├── main.jsx / index.css
        ├── components/
        │   ├── DemoSection.jsx
        │   ├── DetectionResults.jsx
        │   ├── DistanceMeasurementPanel.jsx
        │   ├── Hero.jsx / Navbar.jsx / Footer.jsx
        ├── services/
        │   ├── api.js             # Fetch client for /api/health, /api/detect, /api/distance
        │   └── mockData.js        # Fallback simulation detection data
        └── utils/
            └── geometry.js        # Client-side 3D distance estimation math
```

### 2.2 Dependency & Environment Audit

#### Backend Dependencies
Currently implicit (unmanaged). Inspecting `import` statements across all Python modules:
- Standard Library: `os`, `sys`, `time`, `math`, `base64`, `io`, `pathlib`
- Web Framework: `Flask`, `Flask-Cors`
- Computer Vision & Imaging: `opencv-python` (or `opencv-python-headless`), `numpy`, `Pillow`
- Deep Learning & Inference: `ultralytics`, `torch`, `torchvision`

**Gaps Identified**:
- No `requirements.txt` or `pyproject.toml`.
- No specification of test dependencies (`pytest`, `pytest-cov`, `requests`, `httpx`, `aiohttp`, `psutil`).
- In production, `opencv-python` requires X11/GL libraries which fail in slim Docker images unless `opencv-python-headless` is used.
- No production WSGI server (`gunicorn` for Linux containers, `waitress` for Windows).

#### Frontend Dependencies
From `frontend/package.json`:
- Runtime:
  - `react`: `^19.3.1`
  - `react-dom`: `^19.3.1`
  - `lucide-react`: `^1.66.0`
- Build / Tooling:
  - `vite`: `^8.3.5`
  - `@vitejs/plugin-react`: `^6.1.2`
  - `@tailwindcss/vite`: `^4.3.3`
  - `tailwindcss`: `^4.3.3`
  - `oxlint`: `^1.89.0`
- Runtime Prerequisites:
  - Node.js >= 18.18.0 (Node 20 LTS or Node 22 recommended).
  - Scripts available: `dev`, `build`, `lint`, `preview`.
  - Missing scripts: `test`, `test:e2e`.

---

## 3. Gap Analysis against ORIGINAL_REQUEST.md

| Requirement | Requirement Scope | Current Repository State | Critical Gaps Identified |
|---|---|---|---|
| **R1** | Automated Evaluation & Accuracy Benchmark Suite (YOLO precision, recall, IoU; monocular distance estimation against calibrated reference scenes; output `benchmark_results.json`) | **Non-existent (0%)** | 1. No calibrated reference scenes with ground-truth coordinates & 3D distances.<br>2. No IoU or Precision/Recall/F1 evaluation calculation engine.<br>3. No distance error metric calculation (|D_est - D_true| / D_true).<br>4. No single CLI benchmark runner command producing `benchmark_results.json`. |
| **R2** | Strict Concurrency & Latency Stress Testing Pipeline (50+ simultaneous clients, P50/P90/P95/P99 percentiles, P95 < 80ms budget or CPU bottleneck profiling, memory leak detection) | **Non-existent (0%)** | 1. No load testing script (no Locust, k6, or async Python harness).<br>2. No percentile calculation logic (P50, P90, P95, P99).<br>3. No memory stability profiler (tracking process RSS over sustained loads using `psutil`).<br>4. Backend `app.py` runs single-threaded Flask development server, incapable of handling 50 concurrent clients cleanly without WSGI. |
| **R3** | Comprehensive Integration and Edge-Case Test Suite (JPEG, PNG, WEBP, Base64 data URLs, multipart form-data, empty images, 0/1 objects, extreme aspect ratios, invalid coords, missing camera calibration) | **Non-existent (0%)** | 1. Zero unit, integration, or schema tests.<br>2. No pytest configuration or test fixtures.<br>3. Backend route exception handling returns HTTP 500 on 0-byte or corrupt payloads instead of predictable HTTP 400.<br>4. No automated validation of all image encodings. |
| **R4** | Containerized Production Deployment (Dockerfile, docker-compose.yml, multi-stage builds, model caching volume/layers, healthcheck directives for both backend and frontend) | **Non-existent (0%)** | 1. No Dockerfile for backend.<br>2. No Dockerfile or Nginx reverse proxy configuration for frontend.<br>3. No `docker-compose.yml` orchestrating the services.<br>4. No healthcheck probes defined.<br>5. No model caching layer or volume mounting for `yolov8n.pt`. |

---

## 4. Deep-Dive Architecture & Implementation Blueprints

### 4.1 Requirement R1: Automated Evaluation & Accuracy Benchmark Suite

#### Architecture
The benchmark suite must be runnable via a single CLI command (e.g., `python -m pytest tests/test_benchmarks.py` or `python scripts/run_benchmarks.py`) and generate `benchmark_results.json`.

```
benchmark_suite/
├── reference_scenes/             # Calibrated test scenes
│   ├── scene_urban_traffic.json  # Annotations + camera intrinsics + ground-truth 3D distances
│   ├── scene_urban_traffic.jpg
│   ├── scene_pedestrian_calib.json
│   └── scene_pedestrian_calib.jpg
├── metrics/
│   ├── detection_evaluator.py    # IoU matching, Precision, Recall, mAP@0.5
│   └── distance_evaluator.py     # Absolute error, relative error %, tolerance bounds
└── run_benchmarks.py             # CLI runner generating benchmark_results.json
```

#### Ground-Truth Distance Verification Formula
In `backend/services/distance_estimator.py`, distance is calculated via perspective projection:
$$Z = \frac{f \cdot H_{\text{real}}}{h_{\text{pixels}}}$$
$$X_{\text{cam}} = \frac{(c_x - c_{\text{img},x}) \cdot Z}{f}, \quad Y_{\text{cam}} = \frac{(c_y - c_{\text{img},y}) \cdot Z}{f}$$
$$D_{\text{3D}} = \sqrt{(X_2 - X_1)^2 + (Y_2 - Y_1)^2 + (Z_2 - Z_1)^2}$$

The benchmark suite verifies that for calibrated reference scenes with known real-world 3D positions:
$$\text{Relative Error} = \frac{|D_{\text{est}} - D_{\text{true}}|}{D_{\text{true}}} \times 100\% \le \tau_{\text{threshold}}$$
Where $\tau_{\text{threshold}}$ is mathematically bounded (e.g. $\le 12.0\%$ error for calibrated focal length and typical perspective angles).

#### Schema of `benchmark_results.json`
```json
{
  "timestamp": "2026-11-01T05:30:00Z",
  "model_evaluated": "yolov8n.pt",
  "detection_metrics": {
    "total_ground_truth_objects": 12,
    "total_detected_objects": 12,
    "true_positives": 11,
    "false_positives": 1,
    "false_negatives": 1,
    "precision": 0.9167,
    "recall": 0.9167,
    "f1_score": 0.9167,
    "mean_iou": 0.842
  },
  "distance_metrics": {
    "total_object_pairs_evaluated": 6,
    "mean_relative_error_pct": 5.42,
    "max_relative_error_pct": 8.75,
    "mean_absolute_error_m": 0.48,
    "tolerance_bound_pct": 12.0,
    "passed_bounded_tolerance": true
  },
  "latency_metrics": {
    "iterations": 50,
    "mean_inference_time_ms": 28.4,
    "min_inference_time_ms": 21.1,
    "max_inference_time_ms": 42.6,
    "std_dev_ms": 3.8
  },
  "summary": "PASS: All acceptance criteria met within bounded tolerances."
}
```

---

### 4.2 Requirement R2: Strict Concurrency & Latency Stress Testing Pipeline

#### Architecture
The stress tester must simulate 50+ concurrent virtual clients without external heavy frameworks by implementing a high-throughput asynchronous client using Python `asyncio` and `aiohttp` or `httpx`.

```
stress_testing/
├── stress_tester.py              # Async concurrent runner (50+ clients)
├── latency_profiler.py           # Percentiles: P50, P90, P95, P99, RPS, error rates
├── memory_profiler.py            # psutil process memory sampler (RSS tracking)
└── run_stress_test.py            # Master CLI orchestrator with performance budgets
```

#### Concurrency & Performance Thresholds
1. **Concurrency**: Sustained 50 simultaneous virtual clients hitting `/api/detect` and `/api/distance`.
2. **Success Rate**: 100% of requests handled cleanly (0% unhandled HTTP 5xx errors).
3. **P95 Latency Budget**:
   - Budget: $P_{95} < 80\text{ms}$ under typical loads.
   - Hardware Constraint Exception: In pure CPU execution on low-core virtual machines, PyTorch inference latency per frame is 25-50ms; with 50 concurrent requests queued on a single process, queue time can exceed 80ms. The stress harness must explicitly measure:
     - Total Round-Trip Time (RTT)
     - Server-side `inference_time_ms`
     - Network & Queue Overhead
     - CPU Utilization and saturation profiling.
4. **Memory Stability**:
   - Sample memory before test: $M_{\text{initial}}$
   - Sample memory continuously during test: $M_{\text{peak}}$
   - Sample memory after test (post-cooldown & GC): $M_{\text{settled}}$
   - Verify: $\Delta M = M_{\text{settled}} - M_{\text{initial}} < 30\text{ MB}$, confirming no memory leaks across thousands of sustained requests.

---

### 4.3 Requirement R3: Comprehensive Integration & Edge-Case Test Suite

#### Edge-Case Matrix & Expected HTTP Behaviors

| Test Scenario | Input Payload / Condition | Expected HTTP Code | Expected Response Schema / Behavior | Current Backend Behavior |
|---|---|---|---|---|
| **Health Check** | GET `/api/health` | `200 OK` | `{"status": "healthy", "yolo_loaded": true, ...}` | Returns 200 OK |
| **JPEG Multipart** | POST `/api/detect` with `image/jpeg` form-data | `200 OK` | `{"success": true, "detections": [...], "inference_time_ms": ...}` | Works |
| **PNG Multipart** | POST `/api/detect` with `image/png` form-data | `200 OK` | `{"success": true, "detections": [...]}` | Works |
| **WEBP Multipart** | POST `/api/detect` with `image/webp` form-data | `200 OK` | `{"success": true, "detections": [...]}` | Works |
| **Raw Base64** | POST `/api/detect` with JSON `{"image_base64": "<b64>"}` | `200 OK` | `{"success": true, "detections": [...]}` | Works |
| **Data URI Base64** | POST `/api/detect` with `data:image/jpeg;base64,...` | `200 OK` | `{"success": true, "detections": [...]}` | Works |
| **Empty File (0-bytes)** | POST `/api/detect` with 0-byte file | `400 Bad Request` | `{"error": "Empty or corrupted file"}` | **Bug**: Crashes with `ValueError`, returns 500! |
| **Corrupted Payload** | POST `/api/detect` with non-image bytes | `400 Bad Request` | `{"error": "Unable to decode provided image"}` | Returns 400 |
| **Unsupported Ext** | POST `/api/detect` with `.gif` or `.bmp` | `400 Bad Request` | `{"error": "Unsupported file extension..."}` | Returns 400 |
| **Missing Image** | POST `/api/detect` with `{}` | `400 Bad Request` | `{"error": "No image provided..."}` | Returns 400 |
| **0 Objects Frame** | POST `/api/detect` on solid black image | `200 OK` | `{"total_objects": 0, "detections": []}` | Works |
| **1 Object Frame** | POST `/api/detect` on single person | `200 OK` | `{"total_objects": 1, "detections": [obj_1]}` | Works |
| **Distance Normal** | POST `/api/distance` with obj_a & obj_b | `200 OK` | `{"success": true, "metrics": {"estimated_relative_distance_m": ...}}` | Works |
| **Distance 1 Object** | POST `/api/distance` with only obj_a | `400 Bad Request` | `{"error": "Both object_a and object_b are required"}` | Returns 400 |
| **Extreme Aspect Ratios** | POST `/api/distance` with height=1px | `200 OK` | Handled via `max(1, height)` without divide-by-zero | Works safely |
| **Missing Camera Params** | POST `/api/distance` without focal_length | `200 OK` | Fallbacks to `0.9 * img_w` | Works |
| **Malformed JSON** | POST `/api/distance` with broken JSON | `400 Bad Request` | `{"error": "Invalid JSON"}` | Returns 500 (Flask force=True bug) |

#### Backend Fixes Recommended:
1. In `backend/utils/image_utils.py`:
   - In `file_to_cv2(file_storage)`: check `if len(data) == 0: return None`.
2. In `backend/routes/api.py`:
   - In `calculate_distance()`: replace `request.get_json(force=True)` with `request.get_json(silent=True)` and return 400 if `data is None`.

---

### 4.4 Requirement R4: Containerized Production Deployment

#### Multi-Service Architecture
The deployment requires two cooperating services orchestrated via `docker-compose.yml`:

```
┌────────────────────────────────────────────────────────┐
│                   Docker Host                          │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │  Frontend Container (Nginx Alpine)             │   │
│   │  - Port 80 (or 5173 on host)                   │   │
│   │  - Serves compiled React 19 / Vite static files │   │
│   │  - Reverse proxies /api/ -> http://backend:5000│   │
│   │  - Healthcheck: wget http://localhost:80/      │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ /api/                      │
│                           ▼                            │
│   ┌────────────────────────────────────────────────┐   │
│   │  Backend Container (Python 3.11-slim)          │   │
│   │  - Port 5000                                   │   │
│   │  - Production Gunicorn WSGI (2 wks, 4 thds)    │   │
│   │  - Model Caching: Local yolov8n.pt baked in    │   │
│   │  - Environment: YOLO_CONFIG_DIR=/app/cache     │   │
│   │  - Healthcheck: curl http://localhost:5000/api/│   │
│   └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

#### Specifications for Docker Assets:

1. **`backend/Dockerfile`**:
   - Base: `python:3.11-slim`
   - Apt-get dependencies: `libglib2.0-0 libgomp1 curl` (note: avoid `libgl1-mesa-glx` by using `opencv-python-headless`)
   - Model Caching: `COPY yolov8n.pt /app/yolov8n.pt` and `ENV YOLO_MODEL=/app/yolov8n.pt`
   - WSGI runner: `gunicorn -w 2 --threads 4 -b 0.0.0.0:5000 "backend.app:create_app()"`
   - Healthcheck: `HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD curl -f http://localhost:5000/api/health || exit 1`

2. **`frontend/Dockerfile`**:
   - Multi-stage build:
     - Stage 1: `node:20-alpine` -> `npm ci`, `npm run build`
     - Stage 2: `nginx:alpine` -> Copy `dist/` to `/usr/share/nginx/html`, copy `nginx.conf`
   - Healthcheck: `HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -q --spider http://localhost:80/ || exit 1`

3. **`frontend/nginx.conf`**:
   - SPA routing: `try_files $uri $uri/ /index.html;`
   - Proxy:
     ```nginx
     location /api/ {
         proxy_pass http://backend:5000/api/;
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_read_timeout 120s;
     }
     ```

4. **`docker-compose.yml`**:
   - Services: `backend` and `frontend`
   - Healthcheck dependencies:
     ```yaml
     frontend:
       depends_on:
         backend:
           condition: service_healthy
     ```
   - Port mappings: `5000:5000` (backend), `80:80` or `5173:80` (frontend).

---

## 5. Required File Additions for Implementation

To bring the project from its current state to 100% compliance with R1, R2, R3, and R4, the following files must be created:

### Infrastructure & Dependencies
1. `requirements.txt`: Core backend runtime dependencies (`Flask`, `Flask-Cors`, `opencv-python-headless`, `ultralytics`, `pillow`, `numpy`, `gunicorn`, `waitress`).
2. `requirements-dev.txt`: Testing & benchmarking dependencies (`pytest`, `pytest-cov`, `httpx`, `aiohttp`, `psutil`, `scipy`).
3. `pyproject.toml` or `pytest.ini`: Pytest configuration, test discovery paths, logging defaults.

### Containerization (R4)
4. `Dockerfile.backend` (or `backend/Dockerfile`)
5. `Dockerfile.frontend` (or `frontend/Dockerfile`)
6. `frontend/nginx.conf`
7. `docker-compose.yml`
8. `.dockerignore`

### Automated Evaluation & Benchmarks (R1)
9. `benchmarks/reference_scenes.py`: Reference scenes with calibrated ground-truth bounding boxes, labels, and real 3D distances.
10. `benchmarks/accuracy_benchmark.py`: Evaluates YOLO precision, recall, IoU, and distance estimation relative error.
11. `scripts/run_benchmarks.py`: Single CLI command to execute benchmarks and output `benchmark_results.json`.

### Concurrency & Latency Stress Testing (R2)
12. `stress_testing/concurrency_runner.py`: Async 50+ virtual client runner measuring throughput, status codes, and P50-P99 latencies.
13. `stress_testing/memory_monitor.py`: Continuous RSS memory tracker detecting leaks.
14. `scripts/run_stress_test.py`: CLI command enforcing performance budgets (<80ms P95 or hardware profiling).

### Comprehensive Test Suite (R3)
15. `tests/conftest.py`: Test fixtures (Flask test client, dummy test images in JPEG, PNG, WEBP, base64 payloads).
16. `tests/test_unit_detector.py`: Unit tests for YOLO detector service.
17. `tests/test_unit_distance.py`: Unit tests for monocular distance projection math and edge cases.
18. `tests/test_unit_image_utils.py`: Unit tests for image conversion and validation.
19. `tests/test_api_endpoints.py`: Integration tests for `/api/health`, `/api/detect`, `/api/distance` across all encodings and edge cases.

### Documentation
20. `BENCHMARK_GUIDE.md`: Copy-pasteable instructions for reproducing benchmarks, stress tests, test suites, and Docker deployment.

---

## 6. Risk & Feasibility Assessment

1. **CPU Inference Latency vs. P95 < 80ms Budget**:
   - *Risk*: When 50 concurrent requests hit a CPU-bound PyTorch YOLO inference server, queuing delays can push response latencies over 80ms.
   - *Mitigation*: The acceptance criteria specifically accounts for this: *"P95 latency measurements for API responses meet the strict performance threshold (< 80ms) or log exact hardware-bound profiling bottlenecks when constrained by CPU inference."* The stress testing harness must profile and log internal `inference_time_ms` vs. queue wait time, distinguishing hardware constraints from code inefficiency.
2. **OpenCV in Slim Linux Containers**:
   - *Risk*: Standard `opencv-python` fails with missing `libGL.so.1` in slim Debian/Ubuntu containers.
   - *Mitigation*: Specify `opencv-python-headless` in `requirements.txt`.
3. **Model Re-download on Container Restart**:
   - *Risk*: Ultralytics attempts to connect to `github.com` to download weights if not found.
   - *Mitigation*: `yolov8n.pt` is already in the project root. Copy it into `/app/` and configure `YOLO_MODEL=/app/yolov8n.pt`.

---
*Analysis completed by explorer_survey_infra.*
