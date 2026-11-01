# Handoff Report: API & Calibration Specification Survey

**Agent**: Specification Miner (API & Calibration)  
**Working Directory**: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\spec_miner_survey`  
**Recipient**: Orchestrator (`6bfc04fe-19d9-4c4a-8967-c21e967d520b`)  
**Date**: 2026-11-01  
**Handoff Type**: Hard (Survey Milestone Complete)  

---

## 1. Observation

Direct code observations from inspecting backend and frontend source files:

1. **Flask Application Factory & Route Definitions**:
   - `backend/app.py:17-18`:
     ```python
     CORS(app, resources={r"/api/*": {"origins": "*"}})
     app.register_blueprint(api_bp, url_prefix="/api")
     ```
   - `backend/app.py:20-31`: Defines `GET /` returning JSON with `project`, `domain`, `api_endpoints`, `status: "Online"`.
   - `backend/app.py:33-40`: Defines 404 handler returning `{"error": "Endpoint not found"}, 404` and 500 handler returning `{"error": "Internal server error"}, 500`.
   - `backend/routes/api.py:29-39`: Defines `GET /api/health` returning `{"status": "healthy", "service": "...", "yolo_loaded": bool, "model_name": str, "load_error": str|None, "domain": str}`.
   - `backend/routes/api.py:41-77`: Defines `POST /api/detect` accepting `multipart/form-data` (file key `image`, optional `conf`, `iou`) or JSON (`image_base64`, optional `filename`, `conf`, `iou`). Returns detection metadata, bboxes, and base64 encoded original and annotated images.
   - `backend/routes/api.py:78-100`: Defines `POST /api/distance` accepting JSON with `object_a`, `object_b`, optional `image_dimensions`, `image_base64`, `focal_length_px`.

2. **Configuration Constants**:
   - `backend/config.py:15-26`:
     ```python
     ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
     MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
     YOLO_MODEL_NAME = os.environ.get("YOLO_MODEL", "yolov8n.pt")
     DEFAULT_CONF_THRESHOLD = 0.25
     DEFAULT_IOU_THRESHOLD = 0.45
     DEFAULT_FOCAL_LENGTH_PX = 800.0
     DEFAULT_REAL_OBJECT_HEIGHT = 1.65
     ```

3. **Pinhole Camera Depth & Distance Equations**:
   - `backend/services/distance_estimator.py:6-12`:
     ```python
     CLASS_REFERENCE_HEIGHTS = {
         "person": 1.70, "bicycle": 1.00, "car": 1.50, "motorcycle": 1.10,
         "bus": 3.20, "train": 3.80, "truck": 3.00, "traffic light": 2.80,
         "chair": 0.85, "bottle": 0.25
     }
     DEFAULT_REFERENCE_HEIGHT = 1.50
     ```
   - `backend/services/distance_estimator.py:32-33`:
     ```python
     if focal_length_px is None or focal_length_px <= 0:
         focal_length_px = round(img_w * 0.9, 1)
     ```
   - `backend/services/distance_estimator.py:64-76`:
     ```python
     # Monocular depth: Z = (f * H_real) / h_pixels
     z1 = (focal_length_px * ref_h_a) / h1
     z2 = (focal_length_px * ref_h_b) / h2

     c_img_x = img_w / 2.0
     c_img_y = img_h / 2.0

     x1_cam = ((cx1 - c_img_x) * z1) / focal_length_px
     y1_cam = ((cy1 - c_img_y) * z1) / focal_length_px
     x2_cam = ((cx2 - c_img_x) * z2) / focal_length_px
     y2_cam = ((cy2 - c_img_y) * z2) / focal_length_px

     dist_3d_meters = math.sqrt((x2_cam - x1_cam)**2 + (y2_cam - y1_cam)**2 + (z2 - z1)**2)
     ```
   - `backend/services/distance_estimator.py:54-57`:
     ```python
     pixel_distance = math.sqrt(delta_x**2 + delta_y**2)
     img_diagonal = math.sqrt(img_w**2 + img_h**2)
     norm_distance_pct = (pixel_distance / img_diagonal) * 100.0
     ```

4. **Reference Ground Truth Scene**:
   - `backend/utils/image_utils.py:40-74`: `generate_sample_traffic_scene(output_path)` generates a $960 \times 600$ px image with Car 1 at `[140, 360, 400, 500]` ($w=260, h=140$) and Car 2 at `[580, 310, 790, 420]` ($w=210, h=110$).

5. **Existing Tests & Dependencies**:
   - Zero test files exist in the entire repository.
   - No `requirements.txt` or `pyproject.toml` exists.

---

## 2. Logic Chain

1. **API Completeness & Contract Verification**:
   - Examining `backend/app.py` and `backend/routes/api.py` reveals the exact public REST surface: 4 endpoints (`GET /`, `GET /api/health`, `POST /api/detect`, `POST /api/distance`).
   - The endpoints expect either multipart form-data or JSON payloads with strict keys (`image`, `image_base64`, `conf`, `iou`, `object_a`, `object_b`, `focal_length_px`).
   - In `backend/routes/api.py`, unhandled exceptions are caught by broad `try...except Exception as e:` blocks returning `500 Internal Server Error`.
   - Missing required keys in `/api/detect` or `/api/distance` return `400 Bad Request`.

2. **Calibration & Geometry Mathematical Consistency**:
   - The depth calculation $Z = \frac{f \cdot H_{real}}{h_{pixels}}$ is consistent between backend (`backend/services/distance_estimator.py:65`) and frontend client calculation (`frontend/src/utils/geometry.js:24`).
   - Back-projection to camera coordinates correctly assumes the principal point at the center of the image plane $((W/2, H/2))$.
   - Relative 3D distance is computed via Euclidean metric across camera frame coordinates $(X, Y, Z)$.
   - For the benchmark reference scene (`traffic_urban.jpg`), the analytical ground truth values are:
     * Car 1 Depth: $Z_1 = \frac{864 \cdot 1.50}{140} = 9.257$ m ($\approx 9.26$ m).
     * Car 2 Depth: $Z_2 = \frac{864 \cdot 1.50}{110} = 11.782$ m ($\approx 11.78$ m).
     * 3D Euclidean Relative Distance: $D_{3D} = 5.66$ m.
     * 2D Pixel Separation: $D_{pixel} = 420.1$ px.
     * Normalized Diagonal Ratio: $D_{norm\%} = 37.1\%$.
   - These values form the exact ground truth tolerances needed for Acceptance Criteria R1.

3. **Vulnerabilities & Error Edge Cases Identified**:
   - Type coercion in `detect_objects` (`float(...)`) throws `ValueError` on non-numeric strings, bubbling into a 500 error instead of a clean 400 Bad Request.
   - In `calculate_distance`, `request.get_json(force=True)` on empty/invalid JSON causes `AttributeError` or `BadRequest` resulting in a 500 error instead of 400 Bad Request.
   - Discrepancy between frontend (`forklift: 2.2`) and backend (missing forklift prior).

---

## 3. Caveats

1. **Ultralytics YOLO Runtime Model Loading**:
   - The YOLO model file `yolov8n.pt` (6.5 MB) is located at the repository root. `YOLODetectorService` falls back gracefully to synthetic detections if Ultralytics or PyTorch is unavailable in a given environment. The test harness must test both paths (live PyTorch inference and simulation fallback).
2. **Missing Test Framework**:
   - Because no test runners or requirement files currently exist, running tests requires first establishing `requirements.txt` with `pytest`, `requests`, `httpx`, `locust` (or `asyncio`/`aiohttp` harness), and `psutil`.

---

## 4. Conclusion

The specification mining survey is complete. All 4 REST endpoints, image ingestion types, request/response schemas, error status codes, mathematical pinhole depth formulas, camera calibration parameters, class height priors, and reference scene ground-truth calculations have been discovered, mathematically verified, and documented in detail in `analysis.md`.

The downstream implementation teams (Test Suite, Concurrency Stress Harness, Evaluation Benchmark, and Containerization) now possess complete mathematical ground-truth values and schema contracts to build against.

---

## 5. Verification Method

To independently verify the discoveries and mathematical equations documented in this report:

1. **Inspect Route & Schema Definitions**:
   - Check `backend/routes/api.py` lines 29-100 to verify routes `/api/health`, `/api/detect`, `/api/distance` and error status codes 200, 400, 500.
   - Check `backend/services/distance_estimator.py` lines 6-12, 32-34, 64-77 to verify class priors, adaptive focal length ($0.9 \cdot W$), and 3D Euclidean projection math.
2. **Verify Mathematical Ground Truth on Reference Scene**:
   - Image dimensions: $W = 960, H = 600$, $f = 864.0$ px.
   - Car 1: bbox `[140, 360, 400, 500]`, $h=140 \implies Z_1 = (864 \times 1.50) / 140 = 9.257$ m.
   - Car 2: bbox `[580, 310, 790, 420]`, $h=110 \implies Z_2 = (864 \times 1.50) / 110 = 11.782$ m.
   - $X_1 = ((270 - 480) \times 9.257) / 864 = -2.25$ m, $Y_1 = ((430 - 300) \times 9.257) / 864 = +1.393$ m.
   - $X_2 = ((685 - 480) \times 11.782) / 864 = +2.795$ m, $Y_2 = ((365 - 300) \times 11.782) / 864 = +0.886$ m.
   - $D_{3D} = \sqrt{(2.795 - (-2.25))^2 + (0.886 - 1.393)^2 + (11.782 - 9.257)^2} = \sqrt{5.045^2 + (-0.507)^2 + 2.525^2} = 5.66$ m.
   - Verify that this exact value is produced by `DistanceEstimatorService.calculate_distance()`.
3. **Invalidation Conditions**:
   - If `backend/routes/api.py` route names, parameters, or schema fields are modified.
   - If `CLASS_REFERENCE_HEIGHTS` values or default focal length calculation is changed.
