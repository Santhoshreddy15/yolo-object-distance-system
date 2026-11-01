# Changes Summary — Worker M3: Integration & Edge-Case Test Suite (R3)

**Milestone**: M3  
**Agent**: Worker M3 (Implementer, QA, Specialist)  
**Parent Agent**: 6bfc04fe-19d9-4c4a-8967-c21e967d520b  
**Date**: 2026-11-01  
**Target Directory**: `tests/`  

---

## 1. Summary of Changes

Milestone 3 delivers the comprehensive Integration, Unit, and Edge-Case Test Suite for the YOLO Object Detection and Distance Measurement System. The test suite is organized into 5 specialized modules, a shared fixture harness (`conftest.py`), local pytest configuration (`pytest.ini`), and a standalone fixture-injecting test runner (`run_tests.py`), comprising **102 tests** with 100% requirement coverage.

---

## 2. File Inventory & Module Breakdown

### 1. `tests/pytest.ini` (121 bytes)
- Standardized pytest execution options:
  - `testpaths = .`
  - `python_files = test_*.py`
  - `python_classes = Test*`
  - `python_functions = test_*`
  - `addopts = -v --tb=short`

### 2. `tests/conftest.py` (7,935 bytes)
- Provides shared pytest fixtures and test data generators:
  - `UnitTestConfig`: Subclasses `Config` setting `TESTING = True`, `DEBUG = False`.
  - `create_synthetic_image`: Generates in-memory synthetic image bytes across JPEG, PNG, and WEBP formats with realistic visual road geometries and vehicles.
  - `app`: Flask application session fixture with CORS and blueprint routing.
  - `client`: Flask test client.
  - `sample_jpeg_bytes`, `sample_png_bytes`, `sample_webp_bytes`: Ingestion format fixtures.
  - `blank_black_image_bytes`: Pure black canvas fixture generating 0 detected objects.
  - `sample_raw_base64`: Raw Base64 string without data URI prefix.
  - `sample_base64_data_url`: Standard `data:image/jpeg;base64,...` data URL.
  - `sample_png_data_url`: Standard `data:image/png;base64,...` data URL.
  - `sample_corrupt_bytes`: Corrupted non-image byte sequence.
  - `sample_zero_bytes`: 0-byte empty payload (`b""`).
  - `synthetic_car_pair`: Calibrated vehicle pair complying with `PROJECT.md` contracts.
  - `synthetic_single_object`: Single object payload lacking `object_b` for pairwise rejection tests.
  - `synthetic_forklift_pair`: Warehouse forklift (2.20m prior) and worker (1.70m) test pair.
  - `optical_bench_calibrated_pair`: Analytical ground truth reference targets for exact mathematical tolerance validation.

### 3. `tests/test_unit_detector.py` (8,173 bytes — 12 Tests)
- Unit tests for `backend/services/yolo_detector.py`:
  - `test_detector_initialization_default`: Validates initialization and `is_loaded` property.
  - `test_detector_initialization_invalid_model`: Validates graceful error capture on invalid weights path.
  - `test_detector_detect_numpy_ndarray`: Tests BGR OpenCV numpy array processing.
  - `test_detector_detect_pil_image`: Tests PIL Image RGB format processing.
  - `test_detector_detect_file_path`: Tests image file path input on disk.
  - `test_detector_detect_unsupported_input_type`: Tests rejection of non-image types (TypeError).
  - `test_detector_detect_nonexistent_file_path`: Tests rejection of missing file paths (ValueError).
  - `test_detector_confidence_threshold_filtering`: Confirms higher confidence filters lower-confidence objects.
  - `test_detector_iou_threshold_parameter`: Validates custom NMS IoU threshold acceptance.
  - `test_detector_detection_field_schema`: Validates complete item schema (`id`, `class_name`, `bbox`, `center`, `width`, `height`, `bottom_center`).
  - `test_detector_bounding_box_clamping`: Confirms coordinates are strictly clamped within image bounds.
  - `test_detector_render_annotations`: Validates visual annotation rendering into ndarray.

### 4. `tests/test_unit_distance.py` (12,694 bytes — 16 Tests)
- Unit tests for `backend/services/distance_estimator.py`:
  - `test_distance_service_initialization`: Clean instantiation.
  - `test_class_reference_heights_priors`: Verifies priors for car (1.50), person (1.70), forklift (2.20), bus (3.20), truck (3.00), bicycle (1.00), motorcycle (1.10).
  - `test_projective_depth_calculation_analytical`: Verifies projective depth $Z = (f \cdot H_{real}) / h_{px}$ against exact analytical ground truth.
  - `test_camera_3d_coordinates_and_euclidean_distance`: Verifies 3D Euclidean separation $D_{3D} = \sqrt{\Delta X^2 + \Delta Y^2 + \Delta Z^2}$.
  - `test_colocated_identical_objects_zero_distance`: Co-located objects produce 0.0m separation.
  - `test_distance_calculation_symmetry`: Confirms $D(A, B) \equiv D(B, A)$ and $px(A, B) \equiv px(B, A)$.
  - `test_unknown_class_fallback_to_default_height`: Unknown class names fall back safely to 1.50m.
  - `test_custom_reference_height_override`: Custom reference heights override physical priors.
  - `test_flexible_center_formats`: Accommodates `center` list, `centroid` dict, or `bbox` array.
  - `test_dimension_extraction_fallbacks`: Recovers height from bbox difference or 100.0 default.
  - `test_zero_and_negative_height_clamping`: Prevents zero-division errors via `max(1.0, h)`.
  - `test_missing_and_invalid_image_dimensions_fallback`: Fallback to 960x600 defaults.
  - `test_adaptive_focal_length_fallback`: Fallback to $0.9 \cdot width$ on missing/invalid focal length.
  - `test_draw_distance_measurement_valid_base64`: Renders visual measurement line, circles, and measurement badge.
  - `test_draw_distance_measurement_corrupted_base64`: Returns `None` without exception on corrupt image.
  - `test_optical_bench_analytical_ground_truth`: Optical bench verification to $< 0.5\%$ error tolerance.

### 5. `tests/test_unit_image_utils.py` (8,686 bytes — 21 Tests)
- Unit tests for `backend/utils/image_utils.py`:
  - `validate_image_file`: Tests valid extensions (.jpg, .jpeg, .png, .webp), rejected extensions (.exe, .sh, .txt, .zip, .bin), missing extensions, missing files, and 0-byte file rejection.
  - `file_to_cv2`: Tests valid FileStorage decoding, None rejection, 0-byte rejection, and corrupted byte sequence rejection.
  - `base64_to_cv2`: Tests JPEG data URL, PNG data URL, raw Base64, whitespace padding, empty strings, prefix without payload, corrupt characters, and non-image payload.
  - `cv2_to_base64`: Tests JPEG and PNG data URL generation, None/empty array handling.
  - `generate_sample_traffic_scene`: Tests synthetic scene file creation and (600, 960, 3) geometry.

### 6. `tests/test_api_endpoints.py` (11,738 bytes — 20 Tests)
- Integration tests for REST API endpoints:
  - `GET /`: Validates 200 OK, project metadata, and advertised endpoints.
  - `GET /`: Method restrictions (POST/PUT/DELETE return 405 Method Not Allowed).
  - `GET /api/health`: Validates 200 OK, service name, YOLO load status, and domain metadata.
  - `GET /api/health`: Method restrictions (POST/PUT/DELETE return 405).
  - `GET /api/unknown_endpoint`: Validates 404 with JSON error `{"error": "Endpoint not found"}`.
  - `POST /api/detect`: Tests all 6 ingestion formats:
    1. Multipart form-data with `.jpg`
    2. Multipart form-data with `.png`
    3. Multipart form-data with `.webp`
    4. JSON with raw Base64 string
    5. JSON with `data:image/jpeg;base64,...` Data URL
    6. JSON with `data:image/png;base64,...` Data URL
  - `POST /api/detect`: Custom `conf` and `iou` thresholds via JSON and multipart forms.
  - `POST /api/detect`: Complete schema verification (`success`, `model_used`, `inference_time_ms`, `image_dimensions`, `total_objects`, `detections`, `original_image`, `annotated_image`, `classes_detected`, `filename`).
  - `POST /api/distance`: Standard vehicle pair calculation, metrics subschema verification, custom reference heights, visual overlay rendering, adaptive focal length fallback ($width \cdot 0.9$), and warehouse forklift scenario.

### 7. `tests/test_edge_cases.py` (18,442 bytes — 33 Tests)
- Comprehensive edge-case and boundary verification (enforcing clean 400 Bad Request error codes and 0 crashes):
  - 0 objects detected (solid black frame -> 200 OK with `total_objects: 0`).
  - 1 object detected (pairwise distance impossible -> 400 Bad Request: `Missing or invalid 'object_b'`).
  - Corrupted image payload via multipart -> 400 Bad Request.
  - 0-byte file uploaded -> 400 Bad Request (`Uploaded image file is empty (0 bytes)`).
  - Unsupported file extensions (.exe, .sh, .txt, .bin) -> 400 Bad Request.
  - Corrupted Base64 characters in JSON -> 400 Bad Request.
  - Valid Base64 of non-image plaintext -> 400 Bad Request.
  - Empty Base64 string `""` and whitespace -> 400 Bad Request.
  - Data URL prefix without payload -> 400 Bad Request.
  - Missing image payload entirely -> 400 Bad Request.
  - Empty JSON request body -> 400 Bad Request.
  - Malformed JSON syntax -> 400 Bad Request.
  - Non-object JSON payload -> 400 Bad Request.
  - Non-numeric `conf` threshold -> 400 Bad Request.
  - Negative and excessive `conf` thresholds -> 400 Bad Request.
  - Non-numeric `iou` threshold -> 400 Bad Request.
  - Negative and excessive `iou` thresholds -> 400 Bad Request.
  - Missing both objects in distance calculation -> 400 Bad Request.
  - Non-dictionary object in distance calculation -> 400 Bad Request.
  - Empty request body in distance calculation -> 400 Bad Request.
  - Malformed JSON in distance calculation -> 400 Bad Request.
  - Non-object JSON in distance calculation -> 400 Bad Request.
  - Negative coordinates in bounding boxes and centers -> 200 OK, zero crash.
  - Inverted bounding box coordinates ($x2 < x1$ or $y2 < y1$) -> 200 OK, computed using `abs()`.
  - Extreme bounding box aspect ratio: horizontal needle (1000x1) -> 200 OK, zero crash.
  - Extreme bounding box aspect ratio: vertical needle (1x800) -> 200 OK, zero crash.
  - Missing camera calibration: null focal length (`"focal_length_px": null`) -> 200 OK, adaptive focal length $width \times 0.9$.
  - Non-positive focal length (0 and negative) -> 400 Bad Request.
  - Non-numeric focal length -> 400 Bad Request.
  - Non-dict `image_dimensions` -> 400 Bad Request.
  - Non-numeric / non-positive custom reference heights -> 400 Bad Request.
  - Corrupted `image_base64` passed for visualization -> 200 OK, `visualization_image: null`, zero crash.

### 8. `tests/run_tests.py` (8,780 bytes)
- Standalone test suite runner with dynamic fixture resolution and deep copy isolation.
- Discovers test classes and test methods across all 5 test modules.
- Formats test-by-test execution status, timing in milliseconds, module summaries, and overall pass rates.
- Supports `--verbose` and `--report-file <path>` CLI arguments.
