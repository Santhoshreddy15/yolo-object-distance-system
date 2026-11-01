# Changes Made — Milestone 2: Concurrency & Latency Stress Testing Pipeline

## Overview
Worker M2 implemented and validated the Concurrency & Latency Stress Testing Pipeline (R2) and the production WSGI server configuration for the YOLO Object Distance System project.

## Created Files

### 1. `backend/wsgi.py`
- **Purpose**: Production WSGI entry point for multi-threaded serving.
- **Key Features**:
  - Exposes `app = create_app(Config)` and `application = app` for WSGI runners such as Waitress (`waitress-serve --port=5000 backend.wsgi:app`), Gunicorn, and uWSGI.
  - Pre-warms the YOLOv8 model cache on server initialization inside an application context, eliminating cold-start lockups and race conditions during high-concurrency request bursts.
  - Multi-threaded runtime fallback hierarchy:
    1. Waitress production server (`from waitress import serve`)
    2. Werkzeug multi-threaded server (`run_simple(..., threaded=True)`)
    3. Python standard library `ThreadingWSGIServer` (`wsgiref.simple_server` + `socketserver.ThreadingMixIn`)
  - Configurable via `HOST`, `PORT`, `THREADS` environment variables (defaults: `127.0.0.1`, `5000`, `16` threads).

### 2. `stress_testing/__init__.py`
- **Purpose**: Package initialization exporting `ConcurrentRunner`, `LatencyProfiler`, and `MemoryTracker`.

### 3. `stress_testing/latency_profiler.py`
- **Purpose**: Statistical latency distribution and hardware CPU bottleneck profiling.
- **Key Features**:
  - Calculates P50, P90, P95, and P99 latency percentiles using numpy or pure Python percentiles fallback.
  - Measures minimum, maximum, mean, standard deviation, request count, success count, failure count, and requests per second (RPS).
  - Inspects CPU hardware: CPU brand/model string, physical and logical core counts via `psutil`, CPU utilization percentage, and CUDA availability via PyTorch.
  - Evaluates P95 against the target performance budget (< 80ms). When constrained by CPU inference under 50+ concurrent requests, accurately diagnoses and logs the exact hardware-bound profiling bottlenecks:
    - Distinguishes server-side YOLO inference time from HTTP / network serialization overhead.
    - Profiles thread contention and queue delay across logical CPU cores.
  - Produces structured reports for JSON serialization and console summaries.

### 4. `stress_testing/memory_tracker.py`
- **Purpose**: Real-time process memory utilization tracking and memory leak detection using `psutil`.
- **Key Features**:
  - Continuously samples RSS and VMS memory across target process and child worker threads/processes at configurable intervals (e.g., 0.25s).
  - Records baseline RSS (MB), peak RSS (MB), and post-load final RSS (MB) after cooling down.
  - Computes memory delta ($\Delta\text{RSS} = \text{final} - \text{baseline}$) and peak delta ($\text{peak} - \text{baseline}$).
  - Performs linear regression over elapsed time to calculate the RSS growth slope (MB/s).
  - Automatically flags memory leaks if post-load delta exceeds the threshold (50MB) with sustained positive slope.

### 5. `stress_testing/concurrent_runner.py`
- **Purpose**: High-throughput asynchronous virtual client load runner.
- **Key Features**:
  - Simulates 50+ simultaneous virtual clients using `asyncio` and `httpx.AsyncClient`.
  - Configured with non-blocking connection pools (`Limits(max_connections=100, max_keepalive_connections=50)`).
  - Targets `/api/detect` using realistic base64 JPEG payload and `/api/distance` with 3D coordinate and bounding box parameters.
  - Supports mixed workloads (50% detect, 50% distance) or dedicated endpoint targeting.
  - Supports both fixed total requests mode (queue-driven) and sustained duration mode (deadline-driven).
  - Feeds per-request timings and status codes directly into `LatencyProfiler`.

### 6. `stress_testing/run_stress_test.py`
- **Purpose**: Unified single-CLI runner for the entire stress testing pipeline.
- **Key Features**:
  - Auto-manages server lifecycle: detects whether port 5000 is already active; if not, launches the production multi-threaded WSGI server in an in-process background daemon thread and waits for healthcheck readiness (`/api/health`).
  - Executes concurrent virtual clients with real-time memory tracking.
  - Validates all acceptance criteria:
    1. 50+ concurrent clients tested
    2. 0% unhandled HTTP 5xx errors
    3. P95 latency < 80ms OR hardware-bound CPU inference bottleneck logged
    4. Memory utilization stable without leaks
  - Emits formatted JSON report to `stress_test_report.json`.
  - Prints rich ANSI console summary table.

### 7. `stress_testing/test_stress_components.py`
- **Purpose**: Unit test suite verifying CPU brand detection, latency percentiles math, bottleneck classification, memory tracker sampling, and payload generation.
