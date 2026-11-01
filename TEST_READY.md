# E2E Test Suite Readiness & Verification Guide

## 1. Test Execution Commands

The E2E test suite can be run via the standalone CLI runner or standard `pytest`:

### Standalone CLI Runner (Recommended)
```bash
# Run all 4 test tiers and generate formatted ASCII summary + JSON report:
python e2e_tests/run_e2e_suite.py --all

# Run specific tiers:
python e2e_tests/run_e2e_suite.py --tier 1
python e2e_tests/run_e2e_suite.py --tier 2
python e2e_tests/run_e2e_suite.py --tier 3
python e2e_tests/run_e2e_suite.py --tier 4

# Run with verbose test-by-test output:
python e2e_tests/run_e2e_suite.py --verbose

# Save structured report to custom path:
python e2e_tests/run_e2e_suite.py --report-file e2e_test_report.json
```

### Pytest Runner
```bash
# Run entire suite with verbose test naming:
pytest e2e_tests/ -v

# Run individual tier test files:
pytest e2e_tests/test_tier1_features.py -v
pytest e2e_tests/test_tier2_boundaries.py -v
pytest e2e_tests/test_tier3_combinations.py -v
pytest e2e_tests/test_tier4_workloads.py -v
```

---

## 2. Test Suite Architecture & Tier Breakdown

| Tier | File Path | Focus Area | Test Count | Minimum Spec | Status |
|------|-----------|------------|:----------:|:------------:|:------:|
| **Tier 1** | `e2e_tests/test_tier1_features.py` | Feature Coverage (Root, Health, Detect, Distance, 404/CORS) | **29** | $\ge 5$ / feature | READY |
| **Tier 2** | `e2e_tests/test_tier2_boundaries.py` | Boundary & Corner Cases (0-byte, corrupt headers, oversized, div-by-zero, negative) | **23** | $\ge 5$ / feature | READY |
| **Tier 3** | `e2e_tests/test_tier3_combinations.py` | Cross-Feature Interactions (Pipeline, multi-class, format invariance, scaling) | **10** | Pairwise / comb | READY |
| **Tier 4** | `e2e_tests/test_tier4_workloads.py` | Real-World Scenarios (Traffic ground truth, forklift safety, optical bench <0.5%) | **6** | Realistic scenes | READY |
| **TOTAL** | `e2e_tests/` | **Complete Opaque-Box E2E Suite** | **68** | — | **READY** |

---

## 3. Feature Verification Checklist

### Feature Coverage Checklist (Tier 1)
- [x] **GET /**: Returns HTTP 200 OK with `project`, `domain`, `status: "Online"`.
- [x] **GET /**: Advertises available API routes (`/api/health`, `/api/detect`, `/api/distance`).
- [x] **GET /**: Rejects mutating HTTP verbs (POST/PUT/DELETE) with 405 Method Not Allowed.
- [x] **GET /api/health**: Returns HTTP 200 OK and validates service identity ("YOLO").
- [x] **GET /api/health**: Validates schema keys (`status`, `service`, `yolo_loaded`, `model_name`, `load_error`, `domain`).
- [x] **GET /api/health**: Rejects mutating verbs (POST/PUT/DELETE) with 405 Method Not Allowed.
- [x] **POST /api/detect (Multipart)**: Accepts valid JPEG, PNG, WEBP files and returns 200 OK.
- [x] **POST /api/detect (Base64)**: Accepts `data:image/jpeg;base64,...` data URLs and raw Base64.
- [x] **POST /api/detect (Thresholds)**: Accepts custom `conf` and `iou` filter parameters.
- [x] **POST /api/detect (Schema)**: Full schema validation: `model_used`, `inference_time_ms`, `image_dimensions`, `detections`, `original_image`, `annotated_image`.
- [x] **POST /api/distance**: Computes monocular projective depth $Z = (f \cdot H) / h$.
- [x] **POST /api/distance**: Computes relative 3D Euclidean distance $D_{3D} = \sqrt{\Delta X^2 + \Delta Y^2 + \Delta Z^2}$.
- [x] **POST /api/distance**: Generates annotated visualization image when base64 image provided.
- [x] **POST /api/distance**: Falls back to $0.9 \cdot width$ when `focal_length_px` is omitted.
- [x] **POST /api/distance**: Yields 0.0m distance for identical co-located objects.
- [x] **Routing & Protocols**: Returns HTTP 404 with JSON body for unknown routes; enables CORS headers on `/api/*`.

### Boundary & Corner Cases Checklist (Tier 2)
- [x] **0-Byte File**: Returns HTTP 400 Bad Request with descriptive message.
- [x] **Empty Base64 String**: Returns HTTP 400 Bad Request.
- [x] **Corrupt Base64 String**: Returns HTTP 400 Bad Request without server crash.
- [x] **Corrupt Image Bytes**: Base64 encoding non-image bytes returns HTTP 400 Bad Request.
- [x] **Unsupported File Extensions**: `.exe`, `.sh`, `.txt`, `.zip` return HTTP 400 Bad Request.
- [x] **Empty Request Body**: Returns HTTP 400 Bad Request.
- [x] **Zero Height Bounding Box**: Defensively clamped (`max(1, h)`) to prevent division by zero.
- [x] **Negative Coordinates**: Negative bounding box and center coordinates handled without crashing.
- [x] **Extreme Aspect Ratios**: Horizontal needle (1000x1) and vertical needle (1x800) execute cleanly.
- [x] **Zero / Negative Focal Length**: Rejected with 400 Bad Request or falls back safely without ZeroDivisionError.
- [x] **Unrecognized Class Name**: Falls back to `DEFAULT_REFERENCE_HEIGHT` (1.50m).
- [x] **Oversized Payloads**: Content-Length >16MB rejected with 413 or 400.
- [x] **Malformed JSON Syntax**: Returns HTTP 400 Bad Request.
- [x] **Solid Black Image**: 0 detected objects returns HTTP 200 OK without crashing.
- [x] **Corrupt Visualization Image**: Failed visualization returns metrics safely with `visualization_image: null`.

### Cross-Feature Combinations Checklist (Tier 3)
- [x] **Detect-to-Distance Pipeline**: Full roundtrip workflow (`/api/detect` -> extract -> `/api/distance`).
- [x] **Multi-Class Pairs**: Car/Person, Bus/Bicycle, Truck/Motorcycle pairwise depth comparisons.
- [x] **Industrial Forklift Support (F4)**: Warehouse forklift class prior (2.20m) tested against worker (1.70m).
- [x] **5-Format Invariance**: Identical scene processed via JPEG, PNG, WEBP, Data URL Base64, and Raw Base64.
- [x] **Focal Length Scaling Invariant**: Projective geometry law verified: $Z(2f) / Z(f) = 2.0$.
- [x] **Distance Symmetry**: Proved $D_{3D}(A, B) \equiv D_{3D}(B, A)$ and $px(A, B) \equiv px(B, A)$.
- [x] **Burst Interleaving**: Alternating requests between detect and distance without state leakage.
- [x] **Flexible Object Contracts**: Supported via `center`, `centroid` dict, and `bbox` array.

### Real-World Workloads Checklist (Tier 4)
- [x] **Urban Traffic Ground Truth**: Evaluated against real photographic traffic scene (`traffic_urban.jpg`).
- [x] **Warehouse Forklift Safety**: Evaluated worker proximity and safety zone detection.
- [x] **Optical Bench Accuracy**: Analytical ground truth targets verified to $< 0.5\%$ error tolerance.
- [x] **Crosswalk Pedestrian Separation**: Pure lateral separation ($\Delta X$) verified against 3D Euclidean distance.
- [x] **Sustained Throughput**: 10 sequential frame cycles processed with 100% success rate.
- [x] **1080p High-Resolution Frame**: Scale-invariant coordinate and distance normalization verified.

---

## 4. Test Verification Artifacts

- **Runner Script**: `e2e_tests/run_e2e_suite.py`
- **Pytest Fixtures**: `e2e_tests/conftest.py`
- **Test Modules**:
  - `e2e_tests/test_tier1_features.py`
  - `e2e_tests/test_tier2_boundaries.py`
  - `e2e_tests/test_tier3_combinations.py`
  - `e2e_tests/test_tier4_workloads.py`
- **Output Report**: `e2e_test_report.json`
- **Infrastructure Docs**: `TEST_INFRA.md`
- **Readiness Guide**: `TEST_READY.md`
