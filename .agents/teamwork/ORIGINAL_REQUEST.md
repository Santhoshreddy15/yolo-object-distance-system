# Original User Request

## Initial Request — 2026-11-01T05:03:52Z

Build a comprehensive test, evaluation benchmark, and production-ready deployment pipeline for the YOLO object detection and monocular distance estimation system, featuring automated accuracy/latency benchmark suites, high-concurrency load testing, containerized deployment, and robust REST APIs.

Working directory: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system
Integrity mode: demo

## Requirements

### R1. Automated Evaluation & Accuracy Benchmark Suite
Build an automated evaluation and benchmark suite that evaluates YOLO object detection accuracy (precision, recall, IoU) and monocular distance estimation accuracy against calibrated reference scenes. The suite must output structured JSON metrics and an easily interpretable summary report.

### R2. Strict Concurrency & Latency Stress Testing Pipeline
Create an automated stress testing pipeline that validates API throughput, latency percentiles (P50, P90, P95, P99), and memory usage under sustained concurrent traffic (50+ simultaneous clients) targeting the detection and distance measurement endpoints. The pipeline must enforce strict performance budgets (P95 latency < 80ms under typical loads) and detect any memory leaks or degradation under load.

### R3. Comprehensive Integration and Edge-Case Test Suite
Implement an automated end-to-end test suite verifying the REST APIs across all supported image input types (JPEG, PNG, WEBP, Base64 data URLs, multipart form-data) and edge cases (empty images, single-object frames, extreme bounding box aspect ratios, invalid coordinates, missing camera calibration).

### R4. Containerized Production Deployment
Deliver a reproducible containerization setup (Dockerfile and multi-service orchestration) packaging both the Flask computer vision backend and Vite frontend with automated healthcheck probes, model caching to prevent re-downloads on restart, and production-ready configuration.

## Acceptance Criteria

### Automated Benchmarking
- [ ] Running a single CLI command executes the full evaluation benchmark suite and produces a structured JSON artifact (`benchmark_results.json`) containing precision, recall, mean inference time, and relative distance estimation error.
- [ ] Ground-truth distance verification confirms that calculated 3D relative distances on calibrated benchmark scenes stay within mathematically bounded tolerances.

### Performance & Stress Testing
- [ ] Automated load test verifies that the API processes requests from at least 50 concurrent virtual clients with 0% unhandled HTTP 5xx errors.
- [ ] P95 latency measurements for API responses meet the strict performance threshold (< 80ms) or log exact hardware-bound profiling bottlenecks when constrained by CPU inference.
- [ ] Memory utilization remains stable across a sustained test run without memory leaks.

### Test Automation & Integrity
- [ ] Test suite executes with 100% pass rate across unit, integration, and API schema verification tests.
- [ ] All edge cases (0 objects, 1 object, corrupted image payload, missing parameters) return clear, predictable HTTP error codes and JSON error messages without server crashes.

### Deployment & Reproducibility
- [ ] Container build (`docker compose build` or equivalent) completes cleanly with zero build errors.
- [ ] Services spin up and pass automated container healthcheck probes on both frontend and backend ports.
- [ ] Comprehensive documentation with exact, copy-pasteable CLI commands to reproduce all benchmarks and tests is provided in `README.md` or `BENCHMARK_GUIDE.md`.
