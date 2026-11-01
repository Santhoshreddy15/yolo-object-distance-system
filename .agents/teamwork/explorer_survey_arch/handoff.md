# Handoff Report: Architecture & Codebase Survey

## 1. Observation

Direct observations from codebase inspection and static analysis:

1. **Repository Layout & Model Weights**:
   - The project root at `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system` contains:
     * `yolov8n.pt` (6,549,796 bytes, YOLOv8 nano model weights).
     * `backend/` directory containing Flask application (`app.py`, `config.py`, `routes/api.py`, `services/`, `utils/`).
     * `frontend/` directory containing React 19 / Vite 8 / Tailwind CSS 4 web client.
     * There is no `requirements.txt`, `pyproject.toml`, `Dockerfile`, or `docker-compose.yml` in the project.

2. **Model Weight Loading & Path Resolution**:
   - In `backend/config.py:19`:
     ```python
     YOLO_MODEL_NAME = os.environ.get("YOLO_MODEL", "yolov8n.pt")
     ```
   - In `backend/services/yolo_detector.py:19`:
     ```python
     self.model = YOLO(self.model_name)
     ```
   - When CWD is not the project root (e.g. running from `backend/`), `YOLO("yolov8n.pt")` fails to locate the root model file and triggers a dynamic HTTP download:
     `Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt to 'yolov8n.pt'`
     This violates the offline caching requirement in R4.

3. **Detection on Bundled Sample Image**:
   - `backend/sample_images/traffic_urban.jpg` is generated via `generate_sample_traffic_scene` (`backend/utils/image_utils.py:40-73`) using colored rectangles and circles.
   - When processed through real YOLOv8 nano at default confidence `0.25`, it yields:
     `Objects: 0 Classes: [] Time ms: ~100ms`.
   - As a result, the live interactive distance measurement panel cannot be demonstrated with `traffic_urban.jpg` unless fallback mock mode is enabled or real photos are uploaded.

4. **Unhandled Exceptions Triggering HTTP 500 (Violating R3)**:
   - **Corrupted Base64**: In `backend/routes/api.py:61-62`, passing malformed base64 to `/api/detect` raises `binascii.Error`, caught by line 75:
     ```python
     except Exception as e:
         return jsonify({"error": f"Detection failed: {str(e)}"}), 500
     ```
     Result: `500 {'error': 'Detection failed: Invalid base64-encoded string...'}` instead of HTTP 400.
   - **Empty Image Upload**: Passing an empty 0-byte file raises OpenCV assertion `!buf.empty()`, caught by line 75, returning HTTP 500.
   - **Malformed JSON on `/api/distance`**: In `backend/routes/api.py:81`, `data = request.get_json(force=True)` raises `werkzeug.exceptions.BadRequest` on invalid JSON, caught by line 98, returning HTTP 500:
     `500 {'error': 'Distance calculation failed: 400 Bad Request: ...'}`.
   - **Null Object Height on `/api/distance`**: Passing `object_a: {"height": None}` causes `max(1, object_a.get("height", 100))` to raise `TypeError`, returning HTTP 500.

5. **Distance Calculation Mathematics**:
   - `backend/services/distance_estimator.py:65-76` implements monocular pinhole perspective projection:
     * $Z = \frac{f \cdot H_{real}}{h_{pixels}}$
     * $X = \frac{(cx - c_{img\_x}) \cdot Z}{f}$
     * $Y = \frac{(cy - c_{img\_y}) \cdot Z}{f}$
     * $D_{3D} = \sqrt{(X_2 - X_1)^2 + (Y_2 - Y_1)^2 + (Z_2 - Z_1)^2}$
   - Default focal length: `round(img_w * 0.9, 1)`.
   - Reference heights: `CLASS_REFERENCE_HEIGHTS` in `distance_estimator.py` lacks `"forklift"` (`2.20m`), which is defined in `frontend/src/utils/geometry.js:17` and used in the warehouse sample scenario.

---

## 2. Logic Chain

1. **Premise 1**: Acceptance criteria R4 mandates "automated healthcheck probes, model caching to prevent re-downloads on restart, and production-ready configuration."
   **Evidence**: Observed `config.py` using bare `"yolov8n.pt"`, which downloads from GitHub whenever executed from a directory other than the project root.
   **Inference 1**: `config.py` must be updated to resolve weights to an absolute directory (`BASE_DIR.parent / "yolov8n.pt"` or `os.environ.get("YOLO_WEIGHTS_PATH")`), and a container setup must bake or volume-mount this file.

2. **Premise 2**: Acceptance criteria R3 mandates "All edge cases (0 objects, 1 object, corrupted image payload, missing parameters) return clear, predictable HTTP error codes and JSON error messages without server crashes."
   **Evidence**: Observed that invalid JSON, corrupted base64 strings, empty image files, and null coordinate fields all trigger uncaught exceptions in `backend/routes/api.py` lines 75 and 98, returning HTTP 500.
   **Inference 2**: Explicit request validation and 400 Bad Request error handlers must be added to `api.py` to prevent 500 internal server errors.

3. **Premise 3**: Acceptance criteria R1 mandates "Running a single CLI command executes the full evaluation benchmark suite and produces a structured JSON artifact (`benchmark_results.json`) containing precision, recall, mean inference time, and relative distance estimation error."
   **Evidence**: The repository contains no benchmark scripts, no labeled ground-truth scenes, and no metric calculations.
   **Inference 3**: Milestone 1 must introduce a benchmark suite (`benchmark/` or `eval/`) containing calibrated reference images with ground-truth 3D positions, bounding box labels, and a runner that exports `benchmark_results.json`.

4. **Premise 4**: Acceptance criteria R2 mandates "Automated load test verifies that the API processes requests from at least 50 concurrent virtual clients with 0% unhandled HTTP 5xx errors" with P95 < 80ms or profiling of CPU bottlenecks.
   **Evidence**: The current development server runs single-threaded via `app.run()`. Under concurrent load, requests will serialize or fail with 5xx unless input validation is hardened and a multi-threaded / multi-worker server (e.g. Gunicorn/Waitress) is used.
   **Inference 4**: Milestone 2 must establish a stress test harness (concurrent Python script or Locust runner) and production WSGI server.

---

## 3. Caveats

- **Docker Environment**: Docker CLI is not installed on the current host system. Container verification must rely on Dockerfile syntax verification and local multi-service testing, or container builds in an environment where Docker daemon is active.
- **Hardware Inference Performance**: YOLOv8 nano inference on this host CPU takes ~80–100ms per image. When running 50 concurrent virtual clients on CPU, P95 latency will exceed the 80ms threshold due to compute constraints. The acceptance criteria explicitly allows: *"or log exact hardware-bound profiling bottlenecks when constrained by CPU inference"*. The load testing pipeline must record this hardware profiling constraint.
- **Synthetic Sample Image**: The only bundled image `traffic_urban.jpg` does not contain real detectable objects. Real photographic reference scenes must be supplied for meaningful detection benchmarks.

---

## 4. Conclusion

The application architecture has solid core components:
1. Ultralytics YOLOv8 nano model is already cached locally (`yolov8n.pt`).
2. Flask endpoints (`/api/health`, `/api/detect`, `/api/distance`) are wired to services.
3. The Vite + React 19 frontend is complete with interactive detection and distance calculation UI.

However, to satisfy `ORIGINAL_REQUEST.md`, four key tracks must be implemented:
- **Track A (Evaluation Suite)**: Calibrated reference benchmark suite outputting `benchmark_results.json`.
- **Track B (Stress Pipeline)**: Concurrent stress testing script profiling P50, P90, P95, P99 latency and memory stability under 50+ clients.
- **Track C (Hardening & Edge Cases)**: Input validation in `api.py` returning HTTP 400 instead of HTTP 500 for corrupted payloads, empty images, and invalid fields.
- **Track D (Containerization)**: Multi-stage Dockerfiles for backend and frontend, `docker-compose.yml`, health checks, and absolute model path resolution.

---

## 5. Verification Method

To independently verify the observations reported:

1. **Verify Local Model Loading & Inspection**:
   ```bash
   python -c "from ultralytics import YOLO; m = YOLO('yolov8n.pt'); print('Classes:', len(m.names))"
   ```
   *Expected output*: `Classes: 80`.

2. **Verify HTTP 500 on Malformed Base64 (Bug in `api.py:62`)**:
   ```bash
   python -c "from backend.app import create_app; c = create_app().test_client(); res = c.post('/api/detect', json={'image_base64': 'bad_str'}); print(res.status_code)"
   ```
   *Current output*: `500` (Should be `400`).

3. **Verify HTTP 500 on Malformed Distance JSON (Bug in `api.py:81`)**:
   ```bash
   python -c "from backend.app import create_app; c = create_app().test_client(); res = c.post('/api/distance', data='invalid', content_type='application/json'); print(res.status_code)"
   ```
   *Current output*: `500` (Should be `400`).

4. **Verify Monocular Math Formulation**:
   Inspect `backend/services/distance_estimator.py` lines 65–76 and verify against pinhole projection equations:
   $$Z = \frac{f \cdot H_{real}}{h_{pixels}}, \quad X = \frac{(cx - c_x) Z}{f}, \quad Y = \frac{(cy - c_y) Z}{f}$$
