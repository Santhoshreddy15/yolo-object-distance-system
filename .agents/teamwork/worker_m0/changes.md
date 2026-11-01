# Worker M0 Changes: Foundational Hardening

**Date**: 2026-11-01  
**Milestone**: M0 (Foundational Hardening)  
**Agent**: Worker M0 (Implementer & QA)

---

## 1. Summary of Changes

Worker M0 completed foundational hardening across dependency management, offline model path anchoring, class priors, and defensive HTTP error handling.

### Files Created:
1. `requirements.txt`
   - Added production requirements: `Flask>=3.0.0`, `flask-cors>=4.0.0`, `opencv-python-headless>=4.8.0.76`, `ultralytics>=8.0.0`, `pillow>=10.0.0`, `numpy>=1.24.0`, `gunicorn>=21.2.0`, `waitress>=2.1.2`.
2. `requirements-dev.txt`
   - Added dev/testing requirements: `-r requirements.txt`, `pytest>=7.4.0`, `pytest-asyncio>=0.23.0`, `requests>=2.31.0`, `httpx>=0.25.0`, `aiohttp>=3.9.0`, `psutil>=5.9.0`.
3. `pyproject.toml`
   - Created PEP 518/621 project configuration with standard build-system (`setuptools>=61.0`), core project dependencies, optional dev dependencies, and pytest configuration pointing to `tests` and `e2e_tests`.

### Files Modified:
4. `backend/config.py`
   - Anchored model resolution using `PROJECT_ROOT = Path(__file__).resolve().parent.parent`.
   - Implemented `resolve_model_path()`:
     - Checks `YOLO_WEIGHTS_PATH` / `YOLO_MODEL` environment variables.
     - Resolves relative or absolute paths.
     - Checks `PROJECT_ROOT / "yolov8n.pt"` (the local 6.5MB model file) first, then `backend / "yolov8n.pt"`.
     - Returns absolute path string so Ultralytics directly loads the weights from disk and never makes network requests to download models.
5. `backend/services/distance_estimator.py`
   - Added `"forklift": 2.20` to `CLASS_REFERENCE_HEIGHTS` (matching frontend geometry priors).
   - Created defensive coordinate extractors (`extract_center`) supporting `center` [x, y], `centroid` {x, y}, and `bbox` [x1, y1, x2, y2].
   - Created defensive dimension extractors (`extract_dim`) supporting `width`, `height`, fallback to `bbox` delta (`x2 - x1`, `y2 - y1`), and default 100.0.
   - Handled null or missing `image_dimensions` (fallback to 960x600).
   - Handled null, negative, or invalid `focal_length_px` (fallback to `0.9 * image_width`).
   - Guarded division by `max(1.0, h)` to prevent division by zero.
   - Added top-level contract keys (`depth_object_a`, `depth_object_b`, `distance_3d_meters`, `pixel_distance`, `normalized_distance_pct`, `focal_length_px`) alongside `metrics` to satisfy both frontend and interface contract specifications in `PROJECT.md`.
   - Handled corrupted or invalid image payloads in `_draw_distance_measurement` without crashing.
6. `backend/utils/image_utils.py`
   - `validate_image_file`: added 0-byte file check via `file_storage.seek(0, os.SEEK_END)`.
   - `file_to_cv2`: added checks for empty file storage, empty byte buffer (0-byte file), and OpenCV decode failure. Raises descriptive `ValueError`.
   - `base64_to_cv2`: added checks for empty string, missing string, data URL prefix without payload, base64 decoding errors, 0-byte decoded data, and OpenCV decode failures. Raises descriptive `ValueError`.
   - `cv2_to_base64`: safely returns empty string if image is None, empty, or not a numpy array.
7. `backend/routes/api.py`
   - `POST /api/detect`:
     - Checks for empty JSON payload or malformed JSON syntax, returning HTTP 400 Bad Request `{"error": ...}`.
     - Validates `conf` parameter is numeric float between 0.0 and 1.0; returns HTTP 400 on invalid values.
     - Validates `iou` parameter is numeric float between 0.0 and 1.0; returns HTTP 400 on invalid values.
     - Validates image presence; returns HTTP 400 if neither `image` file nor `image_base64` is provided.
     - Catches `ValueError` from `file_to_cv2` and `base64_to_cv2` (0-byte file, corrupt base64, OpenCV decode failure) and returns HTTP 400 Bad Request with informative error description.
     - Ensures unhandled exceptions during inference return HTTP 500 JSON without server crashing.
   - `POST /api/distance`:
     - Checks for empty request body and malformed JSON, returning HTTP 400 Bad Request `{"error": ...}`.
     - Validates `object_a` and `object_b` presence and type; returns HTTP 400 if missing or not an object.
     - Validates `image_dimensions` is an object if provided; returns HTTP 400 otherwise.
     - Validates `focal_length_px` is numeric and > 0 if provided; returns HTTP 400 otherwise.
     - Validates `custom_ref_height_a` and `custom_ref_height_b` are numeric and > 0 if provided; returns HTTP 400 otherwise.
     - Catches `ValueError` from estimator and returns clean HTTP 400 Bad Request `{"error": ...}`.

---

## 2. Verification Summary

| Component | Test Scenario | Expected Result | Verified Status |
|---|---|---|---|
| Model Path | `backend/config.py` path resolution | Resolves to existing absolute path `yolov8n.pt` (6.5MB) | PASS |
| Packaging | `requirements.txt` dependencies | All 8 packages specified with versions | PASS |
| Packaging | `requirements-dev.txt` dependencies | dev & stress packages specified | PASS |
| Packaging | `pyproject.toml` configuration | PEP 621 compliant, pytest configured | PASS |
| Class Priors | `distance_estimator.py` forklift height | `CLASS_REFERENCE_HEIGHTS["forklift"] == 2.20` | PASS |
| Fallbacks | `distance_estimator.py` null height / bbox | Gracefully extracts from bbox or defaults to 100.0 | PASS |
| Fallbacks | `distance_estimator.py` null dimensions | Gracefully falls back to 960x600 and computed focal | PASS |
| Validation | `POST /api/detect` empty JSON payload | Returns HTTP 400 with `{"error": "Empty JSON payload"}` | PASS |
| Validation | `POST /api/detect` invalid JSON syntax | Returns HTTP 400 with `{"error": "Invalid JSON payload..."}` | PASS |
| Validation | `POST /api/detect` non-numeric conf / iou | Returns HTTP 400 with `{"error": "Invalid 'conf' threshold..."}` | PASS |
| Validation | `POST /api/detect` out-of-bounds conf (>1.0) | Returns HTTP 400 with `{"error": "Confidence threshold must be..."}` | PASS |
| Validation | `POST /api/detect` missing image | Returns HTTP 400 with `{"error": "No image provided..."}` | PASS |
| Validation | `POST /api/detect` corrupted base64 | Returns HTTP 400 with `{"error": "Corrupted or invalid base64..."}` | PASS |
| Validation | `POST /api/detect` 0-byte decoded base64 | Returns HTTP 400 with `{"error": "Decoded base64 image data is empty..."}` | PASS |
| Validation | `POST /api/detect` non-image base64 bytes | Returns HTTP 400 with `{"error": "Unable to decode image from base64..."}` | PASS |
| Validation | `POST /api/distance` empty request body | Returns HTTP 400 with `{"error": "Empty request body..."}` | PASS |
| Validation | `POST /api/distance` missing object_a / b | Returns HTTP 400 with `{"error": "Missing or invalid 'object_a'..."}` | PASS |
| Validation | `POST /api/distance` non-numeric focal length | Returns HTTP 400 with `{"error": "Invalid 'focal_length_px'..."}` | PASS |
| Contract | `POST /api/distance` response schema | Includes `depth_object_a`, `depth_object_b`, `distance_3d_meters`, `metrics` | PASS |
