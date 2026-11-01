# Dispatch: Milestone 2 Worker — Concurrency & Latency Stress Testing Pipeline (R2)

Your working directory: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\worker_m2`
Project root: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system`
Scope document: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\PROJECT.md`
Original request: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\ORIGINAL_REQUEST.md`

File ownership (exclusive):
- `stress_testing/` (all files: `concurrent_runner.py`, `latency_profiler.py`, `memory_tracker.py`, `run_stress_test.py`)
- `backend/wsgi.py` (production WSGI entry point for Waitress / Gunicorn)
- `stress_test_report.json`

Requirements to fulfill:
1. Multi-Threaded WSGI Server:
   - Provide `backend/wsgi.py` allowing running with Waitress on Windows (`waitress-serve --port=5000 backend.wsgi:app`) or Gunicorn on Linux.
2. High-Concurrency Stress Testing Pipeline:
   - Automated stress testing pipeline in `stress_testing/run_stress_test.py` that targets `/api/detect` and `/api/distance`.
   - Uses `asyncio` + `httpx`/`aiohttp` (or Locust) to generate sustained concurrent traffic from at least 50 simultaneous virtual clients.
   - Validates 0% unhandled HTTP 5xx errors across all 50+ concurrent clients.
3. Latency Percentiles & CPU Bottleneck Profiling:
   - Computes P50, P90, P95, P99 latency percentiles and requests/sec throughput.
   - Enforces strict performance budgets: checks if P95 < 80ms under typical loads. When running CPU inference where compute bounds exceed 80ms (e.g. YOLOv8 nano CPU inference taking ~80-100ms per frame), accurately logs and documents the exact hardware-bound profiling bottlenecks (CPU model, thread utilization, inference vs network latency breakdown) as explicitly permitted in the acceptance criteria.
4. Memory Leak Detection:
   - Monitors RSS memory utilization (MB) using `psutil` at start, during, and after sustained test load.
   - Measures memory slope / delta to verify that memory remains stable without memory leaks.
5. CLI Runner & Output:
   - Produces structured JSON artifact `stress_test_report.json` and human-readable terminal summary.
   - Single CLI command: `python stress_testing/run_stress_test.py`.
6. Run the stress test pipeline using `run_command`, verify all metrics, and document in handoff report.


## 2026-11-01T05:48:26Z
You are Worker M2 for the YOLO Object Distance System project.
Your working directory is: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\worker_m2
Project root: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system
Scope document: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\PROJECT.md

MANDATORY: You MUST read ORIGINAL_REQUEST.md before starting work:
Path: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File ownership (exclusive):
- stress_testing/ (all files: concurrent_runner.py, latency_profiler.py, memory_tracker.py, run_stress_test.py)
- backend/wsgi.py
- stress_test_report.json

Tasks:
1. Read DISPATCH.md in your working directory.
2. Provide backend/wsgi.py for multi-threaded production serving.
3. Implement the Concurrency & Latency Stress Testing Pipeline in stress_testing/:
   - Async concurrent client runner simulating 50+ simultaneous virtual clients targeting /api/detect and /api/distance.
   - Verifies 0% unhandled HTTP 5xx errors under load.
   - Computes P50, P90, P95, P99 latency percentiles and throughput. Enforces P95 < 80ms or profiles exact hardware-bound CPU bottlenecks.
   - Tracks memory usage (RSS MB) via psutil to detect memory leaks over sustained runs.
   - Single-CLI runner: python stress_testing/run_stress_test.py generating stress_test_report.json and console summary.
4. Run the stress test pipeline using run_command, verify that 50+ concurrent requests succeed with 0% 5xx errors, and document exact outputs.
5. Write changes.md and handoff.md in your working directory.
6. Send a completion message to orchestrator (6bfc04fe-19d9-4c4a-8967-c21e967d520b).


## 2026-11-01T05:51:53Z
**Context**: Milestone Execution
**Content**: Please ensure all implementation files, code modules, test scripts, and configurations are fully created using write_to_file before running any commands. Avoid blocking commands. If package installation is not possible or pending, implement pure-Python and standard-library fallbacks (e.g. wsgiref/waitress/asyncio/httpx).
**Action**: Create all your assigned files using write_to_file, verify via self-contained python test scripts or static validation, write changes.md and handoff.md, and send your completion report.
