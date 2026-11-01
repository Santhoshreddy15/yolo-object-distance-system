# E2E Test Infrastructure Specification

## 1. Test Philosophy & Principles

The End-to-End (E2E) Test Suite for the **YOLO Object Detection & Monocular Distance Measurement System** is designed and implemented under the following core tenets:

1. **Requirement-Driven & Opaque-Box**:
   Tests validate system contracts from the perspective of an external API consumer. The internal implementation details (PyTorch, Ultralytics, OpenCV, math transforms) are treated as opaque; tests evaluate observable HTTP responses, status codes, JSON payload schemas, bounding box geometries, and physical 3D distance metrics.

2. **Progressive Testability & No Facades**:
   No mock facades or tautological tests that pass without executing real logic. Tests exercise real Flask WSGI routing, image decoding, projective geometry, and error-handling pipelines.

3. **Deterministic Output & Ground-Truth Derivation**:
   Expected values are mathematically derived from analytical projective pinhole optics:
   $$Z = \frac{f \cdot H_{real}}{h_{pixels}}$$
   $$X = \frac{(cx - c_x) \cdot Z}{f}, \quad Y = \frac{(cy - c_y) \cdot Z}{f}$$
   $$D_{3D} = \sqrt{\Delta X^2 + \Delta Y^2 + \Delta Z^2}$$
   Analytical reference scenes (e.g., optical bench calibration targets) enforce strict mathematical bounds ($\le 0.5\%$ error tolerance).

4. **Zero 500 Defect Budget**:
   The API must never crash with unhandled HTTP 500 Internal Server Errors on malformed, corrupted, truncated, or adversarial inputs. All client errors must return deterministic, descriptive HTTP 400 Bad Request (or 413 Payload Too Large / 405 Method Not Allowed) responses.

---

## 2. Test Harness Architecture

The test harness (`e2e_tests/`) provides both in-memory WSGI and live-server testing:

```
e2e_tests/
├── conftest.py                # Session fixtures, test client, synthetic image generators
├── test_tier1_features.py     # Tier 1: Feature Coverage (>=5 tests per feature)
├── test_tier2_boundaries.py   # Tier 2: Boundary & Corner Cases (>=5 tests per feature)
├── test_tier3_combinations.py # Tier 3: Cross-Feature Combinations & Invariance
├── test_tier4_workloads.py    # Tier 4: Real-World Scenarios & Calibrated Benchmarks
└── run_e2e_suite.py           # Standalone CLI runner with ASCII report & JSON logging
```

### Dual-Mode Execution:
- **In-Memory WSGI (`client`)**: Uses Flask's native `test_client()` for rapid, deterministic execution with 0 network port conflicts, testing the complete WSGI stack.
- **Standalone CLI Runner (`run_e2e_suite.py`)**: Executes the entire suite with dependency-injected test functions, generates ASCII tabular reports, logs structured JSON metrics, and returns clean exit codes.
- **Pytest Compatible**: Every test file follows standard pytest conventions (`test_*.py`) and works seamlessly with `pytest e2e_tests/`.

---

## 3. Four-Tier Test Matrix

| Tier | Focus Area | Test Count | Key Invariants Tested |
|------|------------|------------|------------------------|
| **Tier 1** | **Feature Coverage** | 29 | Status 200 on all endpoints, schema validation, projective depth formulas, visualization rendering, 404/CORS/405 |
| **Tier 2** | **Boundary & Corner Cases** | 23 | 0-byte images, corrupt base64, garbage bytes, invalid extensions, height=0 division prevention, negative coords, oversized headers |
| **Tier 3** | **Cross-Feature Combinations** | 10 | Detect -> extract -> distance pipeline, 5 image formats (JPEG/PNG/WEBP/DataURL/Raw), focal scaling $Z(2f)=2Z(f)$, distance symmetry |
| **Tier 4** | **Real-World Workloads** | 6 | Urban traffic ground truth, warehouse forklift proximity zone, optical bench calibration (<0.5% error), crosswalk lateral separation |
| **TOTAL** | **Full System Suite** | **68** | **Comprehensive end-to-end verification** |

### Tier Breakdown Details

#### Tier 1: Feature Coverage (29 Tests)
- **Feature 1 (`GET /`)**: 5 tests — Status 200, Content-Type `application/json`, metadata fields (`project`, `domain`, `status`), advertised endpoints list, method rejection (POST/PUT/DELETE -> 405).
- **Feature 2 (`GET /api/health`)**: 5 tests — Status 200, Content-Type `application/json`, schema keys (`status`, `service`, `yolo_loaded`, `model_name`, `load_error`, `domain`), service identity, method rejection -> 405.
- **Feature 3 (`POST /api/detect`)**: 7 tests — Multipart JPEG upload, Multipart PNG upload, Multipart WEBP upload, JSON Base64 Data URL, JSON Raw Base64, custom `conf`/`iou` thresholds, response schema & bounding box structure.
- **Feature 4 (`POST /api/distance`)**: 7 tests — Standard two-vehicle calculation, complete metrics schema, projective pinhole depth derivation ($Z_1, Z_2$), visualization image rendering, default focal length fallback ($0.9 \cdot width$), co-located object zero distance, method rejection -> 405.
- **Feature 5 (Global Protocol & Routing)**: 5 tests — 404 route handling, 404 JSON body structure, CORS headers, HEAD requests, OPTIONS preflight requests.

#### Tier 2: Boundary & Corner Cases (23 Tests)
- **Detection Boundaries**: 0-byte multipart file (400), empty base64 string (400), corrupt base64 encoding (400), valid base64 non-image bytes (400), unsupported extensions (.exe/.sh/.txt -> 400), missing payload (400), solid black image (200 with 0 detections), 1x1 micro image (200).
- **Distance Boundaries**: Missing `object_a` (400), missing `object_b` (400), empty JSON body (400), zero height bounding box (clamped to max(1, h) preventing division by zero), negative coordinates, horizontal needle aspect ratio (1000x1), vertical needle aspect ratio (1x800), zero/negative focal length, unrecognized class prior fallback (1.50m).
- **Protocol & Payload Boundaries**: Content-Length >16MB (413/400), malformed JSON syntax (400), boundary conf thresholds (0.0 and 1.0), null image dimensions fallback, corrupt visualization base64 graceful fallback.

#### Tier 3: Cross-Feature Combinations (10 Tests)
- End-to-end pipeline: POST `/api/detect` $\to$ extract detections $\to$ POST `/api/distance` with base64 visual.
- Multi-class pairwise combinations: Car vs Person, Bus vs Bicycle, Forklift vs Worker.
- 5-Format Invariance: Multipart JPEG, Multipart PNG, Multipart WEBP, Base64 Data URL, Raw Base64.
- Geometric Invariants: Focal length linear scaling $Z(2f) = 2 \cdot Z(f)$.
- Distance Symmetry: $D_{3D}(A, B) \equiv D_{3D}(B, A)$.
- Flexible Object Contracts: Center array `[x, y]`, centroid dict `{"x": ..., "y": ...}`, or bounding box `[x1, y1, x2, y2]`.
- Consecutive interleaved burst stability: 10 alternating detect/distance requests without memory/state leakage.

#### Tier 4: Real-World Scenarios (6 Tests)
- **Urban Traffic Ground Truth**: Evaluation on calibrated photographic traffic scene (`traffic_urban.jpg`), verifying calculated vehicle separation is bounded within realistic road limits [2m, 25m].
- **Warehouse Safety Zone**: Industrial forklift proximity monitoring to ensure pedestrian worker safety warning radius is accurately quantifiable.
- **Calibrated Optical Bench**: Targets placed at analytical depths $Z_A = 5.0$m and $Z_B = 10.0$m with known focal length $f=800$px; enforces $< 0.5\%$ error tolerance against analytical truth.
- **Crosswalk Lateral Separation**: Two pedestrians walking abreast at identical depth ($Z_1 = Z_2 = 8.0$m); verifies calculated 3D distance strictly measures real-world lateral separation $\Delta X$.
- **Sustained Stream Throughput**: 10 sequential frame cycles to verify zero performance degradation or memory accumulation.
- **High-Resolution Monitoring (1080p)**: 1920x1080 full HD camera frames verifying scale-invariant normalized distance percentage and coordinates.

---

## 4. Coverage Thresholds & Quality Gates

The test suite enforces the following mandatory quality gates:

1. **Pass Rate Threshold**: 100% (68 / 68 tests passing).
2. **Unhandled 500 Errors**: 0% allowed. Any client-side error must return HTTP 400 / 413 / 405.
3. **Response Schema Compliance**: 100% of responses must adhere to interface contracts in `PROJECT.md`.
4. **Analytical Accuracy**: Optical bench calibration distance errors must remain $< 0.5\%$.
5. **Execution Speed**: The complete 68-test in-memory suite must execute in $< 5.0$ seconds.
