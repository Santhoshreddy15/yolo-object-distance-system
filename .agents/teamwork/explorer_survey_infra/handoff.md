# Infra & Testing Survey Handoff Report

**Agent**: `explorer_survey_infra`  
**Milestone**: Survey Phase  
**Target Path**: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system`  
**Working Directory**: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\explorer_survey_infra`  

---

## 1. Observation

Direct observations from inspecting the codebase:

1. **Repository Structure**:
   - `find_by_name` at root `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system` found 45 files.
   - Project contains `backend/` (Flask application), `frontend/` (React Vite application), and root file `yolov8n.pt` (6,549,796 bytes).
2. **Tests**:
   - `find_by_name` for pattern `*test*` returned 0 test files in `backend/` or `frontend/`.
   - No `tests/` directory, no `pytest.ini`, no `pyproject.toml`, no test mocks, and no test scripts exist anywhere in the repository.
   - In `frontend/package.json` (lines 6-11):
     ```json
     "scripts": {
       "dev": "vite",
       "build": "vite build",
       "lint": "oxlint",
       "preview": "vite preview"
     }
     ```
     No frontend test runner is configured.
3. **Backend Dependencies & Package Management**:
   - No `requirements.txt`, `pyproject.toml`, `Pipfile`, or `setup.py` exists anywhere in the repository.
   - Code inspection reveals imports:
     - `backend/app.py` (lines 3-4): `from flask import Flask, jsonify`, `from flask_cors import CORS`
     - `backend/routes/api.py` (lines 2-4): `import cv2`, `from flask import Blueprint, request, jsonify, current_app`
     - `backend/services/yolo_detector.py` (lines 4-6, 18): `import cv2`, `import numpy as np`, `from PIL import Image`, `from ultralytics import YOLO`
     - `backend/services/distance_estimator.py` (lines 3-4): `import cv2`, `import numpy as np`
     - `backend/utils/image_utils.py` (lines 2-5): `import cv2`, `import numpy as np`, `from PIL import Image`
4. **Containerization**:
   - Neither `backend/` nor `frontend/` nor project root contains a `Dockerfile`, `docker-compose.yml`, or `.dockerignore`.
   - In `backend/app.py` (lines 43-47):
     ```python
     if __name__ == "__main__":
         app = create_app()
         port = int(os.environ.get("PORT", 5000))
         print(f"[INFO] Starting YOLO Object Detection & Distance Measurement Backend on http://127.0.0.1:{port}")
         app.run(host="127.0.0.1", port=port, debug=False)
     ```
     The server is configured only to run the local Flask development server on `127.0.0.1`, not `0.0.0.0` or a production WSGI runner.
5. **Benchmarking & Stress Testing**:
   - No benchmark scripts exist to compute YOLO detection precision, recall, or IoU.
   - No calibrated reference scenes with ground-truth distance data exist.
   - No stress testing scripts (Locust, k6, or async Python runners) exist.
   - No latency percentile collector (P50, P90, P95, P99) exists.
   - No memory profiling (e.g. using `psutil`) exists.
6. **API Error Handling & Edge Cases**:
   - In `backend/utils/image_utils.py` (lines 17-24):
     ```python
     def file_to_cv2(file_storage):
         in_memory_file = io.BytesIO()
         file_storage.save(in_memory_file)
         data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
         image = cv2.imdecode(data, cv2.IMREAD_COLOR)
         if image is None:
             raise ValueError("Could not decode image from file bytes")
         return image
     ```
     If an empty file (0 bytes) is uploaded, `ValueError` is raised. In `backend/routes/api.py` (lines 75-76), this is caught by `except Exception as e: return jsonify({"error": f"Detection failed: {str(e)}"}), 500`, returning HTTP 500 instead of HTTP 400.
   - In `backend/routes/api.py` (line 81): `data = request.get_json(force=True)`. If invalid/malformed JSON is supplied, Flask raises a 400 or 500 BadRequest.

---

## 2. Logic Chain

1. **Premise 1 (R1 - Benchmarks)**: Requirement R1 mandates an automated benchmark suite evaluating YOLO detection accuracy (precision, recall, IoU) and monocular distance estimation against calibrated reference scenes, producing a structured artifact `benchmark_results.json`.
   - *Observation*: Zero benchmark scripts, zero calibrated reference scene datasets, and zero metric calculation scripts currently exist.
   - *Inference*: A complete benchmark suite (`benchmarks/` and `scripts/run_benchmarks.py`) must be built from scratch, including reference scene ground-truth definitions, IoU computation, precision-recall computation, 3D distance error verification, and structured JSON output generation.
2. **Premise 2 (R2 - Stress Testing)**: Requirement R2 mandates an automated stress testing pipeline validating throughput, latency percentiles (P50, P90, P95, P99), and memory usage under sustained concurrent traffic (50+ simultaneous clients) with P95 < 80ms or CPU bottleneck profiling.
   - *Observation*: The repository currently only runs a single-threaded Werkzeug development server on `127.0.0.1` and has zero load testing tools or scripts.
   - *Inference*: 
     a. An asynchronous 50+ virtual client stress testing pipeline (`stress_testing/run_stress_test.py`) using `asyncio` and `httpx`/`aiohttp` with `psutil` memory tracking must be created.
     b. A production WSGI server (`gunicorn` with worker/thread configuration) must be introduced to handle concurrent requests without dropping connections.
     c. Latency profiling must log both total round-trip time and internal model inference time to properly attribute hardware constraints when running on CPU.
3. **Premise 3 (R3 - Integration & Edge Cases)**: Requirement R3 mandates an automated test suite verifying REST APIs across all supported image input types (JPEG, PNG, WEBP, Base64 data URLs, multipart form-data) and edge cases with 100% pass rate and clear HTTP error codes without server crashes.
   - *Observation*: Zero test suites exist; 0-byte file uploads and malformed payloads trigger HTTP 500 rather than predictable HTTP 400.
   - *Inference*:
     a. A comprehensive `pytest` test suite must be built covering unit tests (`test_unit_detector.py`, `test_unit_distance.py`, `test_unit_image_utils.py`) and integration tests (`test_api_endpoints.py`).
     b. Minor defensive handling fixes in `image_utils.py` and `api.py` are required so corrupt/empty inputs predictably return HTTP 400.
4. **Premise 4 (R4 - Containerization)**: Requirement R4 mandates a reproducible containerization setup (Dockerfile and multi-service orchestration) packaging both Flask backend and Vite frontend with automated healthchecks, model caching, and production configuration.
   - *Observation*: Zero Dockerfiles, zero compose files, zero Nginx configurations, and zero healthcheck probes exist.
   - *Inference*:
     a. `backend/Dockerfile` with `python:3.11-slim`, `opencv-python-headless`, baked-in `yolov8n.pt`, Gunicorn, and healthcheck probe must be created.
     b. `frontend/Dockerfile` with multi-stage build (Node 20 builder -> Nginx runner) and reverse proxy `/api/` to backend must be created.
     c. `docker-compose.yml` linking both services with healthcheck dependency must be created.
5. **Premise 5 (Dependencies)**:
   - *Observation*: Python dependencies are completely unpinned and unlisted.
   - *Inference*: `requirements.txt` (runtime) and `requirements-dev.txt` (testing, benchmarks, stress testing) must be created immediately as foundational prerequisites.

---

## 3. Caveats

1. **Hardware Constraints on P95 Latency (< 80ms)**:
   - YOLOv8 nano CPU inference typically requires 25ms to 55ms per single frame on modern x86_64 CPUs.
   - Under 50 concurrent requests queued on a CPU with limited cores, queue wait time will push P95 latency beyond 80ms unless hardware has sufficient CPU threads or concurrency is batched.
   - The stress test suite must distinguish between hardware-bound inference bottlenecks and software/network bugs, as explicitly specified in the acceptance criteria.
2. **Command Execution Restriction in Subagent**:
   - Direct shell command execution was denied in the environment during the survey turn; all findings are established via exhaustive static inspection of the filesystem and source code files.
3. **Model Weights Invalidation**:
   - `yolov8n.pt` is 6.5 MB in size. In containerization, copying this file directly into the container prevents any runtime download dependencies. If the file is modified or corrupted, ultralytics will attempt an external network call to GitHub unless blocked.

---

## 4. Conclusion

The repository currently contains the bare application code for Flask and React, but **lacks 100% of the testing, benchmarking, load testing, dependency management, and containerization infrastructure** required by R1, R2, R3, and R4 in `ORIGINAL_REQUEST.md`.

To satisfy all acceptance criteria, the implementation plan must construct:
1. **Dependencies**: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`.
2. **R1**: Calibrated reference scenes dataset, IoU & precision/recall metric evaluator, relative distance error verification engine, and single-CLI benchmark runner producing `benchmark_results.json`.
3. **R2**: Async 50+ virtual client load generator, P50/P90/P95/P99 latency profiler, `psutil` memory leak detector, and CPU bottleneck reporter.
4. **R3**: Pytest unit & integration test suite covering JPEG, PNG, WEBP, raw Base64, data URI Base64, and all edge cases (0 objects, 1 object, corrupt bytes, 0-byte files, extreme aspect ratios, missing calibration), plus minor defensive error handling fixes in `image_utils.py` and `api.py`.
5. **R4**: Multi-stage `frontend/Dockerfile` (Node 20 -> Nginx proxy), `backend/Dockerfile` (Python 3.11-slim + Gunicorn + model caching + healthcheck), `docker-compose.yml`, and `BENCHMARK_GUIDE.md`.

---

## 5. Verification Method

To independently verify these survey findings:

1. **Verify Absence of Tests and Configurations**:
   ```powershell
   Get-ChildItem -Path "C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system" -Recurse -Filter "*test*"
   Get-ChildItem -Path "C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system" -Recurse -Include "requirements.txt", "Dockerfile*", "docker-compose.yml", "pytest.ini"
   ```
   *Expected Result*: No matching test files or infrastructure configuration files returned.
2. **Verify Detailed Analysis**:
   - Inspect `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\explorer_survey_infra\analysis.md`.
3. **Invalidation Conditions**:
   - If any `tests/` directory, `Dockerfile`, or `requirements.txt` already exists in another uninspected branch or folder, this survey's conclusion of 0% pre-existing test/infra code would be invalidated.
