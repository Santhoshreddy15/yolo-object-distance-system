#!/usr/bin/env python3
"""
Single-CLI Runner for YOLO Object Distance System Stress Testing Pipeline.
Validates:
- 50+ concurrent virtual clients targeting /api/detect and /api/distance
- 0% unhandled HTTP 5xx errors
- P50, P90, P95, P99 latency distribution & hardware CPU bottleneck diagnosis
- RSS memory leak detection across sustained load
- Outputs structured stress_test_report.json and ANSI console summary.
"""

import argparse
import datetime
import json
import os
import platform
import socket
import sys
import threading
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
import psutil

from stress_testing.latency_profiler import LatencyProfiler, get_cpu_brand_name
from stress_testing.memory_tracker import MemoryTracker
from stress_testing.concurrent_runner import ConcurrentRunner


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check whether a local port has an active listener."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def wait_for_server(url: str, timeout_sec: float = 10.0) -> bool:
    """Poll health endpoint until server responds or timeout expires."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{url}/api/health")
                if resp.status_code == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def start_inprocess_server(port: int = 5000, host: str = "127.0.0.1"):
    """
    Launch production WSGI application in a background daemon thread
    using Werkzeug's multi-threaded server or ThreadingWSGIServer.
    """
    from backend.wsgi import app
    try:
        from werkzeug.serving import make_server
        server = make_server(host, port, app, threaded=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
    except ImportError:
        from socketserver import ThreadingMixIn
        from wsgiref.simple_server import WSGIServer, make_server

        class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
            daemon_threads = True
            allow_reuse_address = True

        server = make_server(host, port, app, server_class=ThreadingWSGIServer)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server


def print_banner(clients: int, total_reqs: int, target_url: str):
    print("=" * 78)
    print("  YOLO OBJECT DISTANCE SYSTEM — CONCURRENCY & LATENCY STRESS TEST PIPELINE")
    print("=" * 78)
    print(f"  Target URL:          {target_url}")
    print(f"  Simulated Clients:   {clients} concurrent virtual clients")
    print(f"  Total Requests:      {total_reqs} requests (mixed /api/detect & /api/distance)")
    print(f"  CPU Hardware:        {get_cpu_brand_name()}")
    print(f"  Logical Cores:       {psutil.cpu_count(logical=True)}")
    print(f"  Timestamp:           {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 78)
    print()


def print_console_summary(report: Dict[str, Any]):
    summary = report["summary"]
    detect = report["endpoints"]["/api/detect"]
    distance = report["endpoints"]["/api/distance"]
    bottleneck = report["bottleneck_profiling"]
    mem = report["memory_metrics"]
    criteria = report["acceptance_criteria"]

    print("\n" + "=" * 78)
    print("                           STRESS TEST RESULTS")
    print("=" * 78)
    print(f"  Total Requests:      {summary['count']} requests")
    print(f"  Successful (2xx):    {summary['successful']} ({100.0 - summary['error_rate_pct']:.1f}%)")
    print(f"  Failed Requests:     {summary['failed']} ({summary['error_rate_pct']:.1f}%)")
    print(f"  Unhandled HTTP 5xx:  {summary['unhandled_5xx_count']} ({summary['unhandled_5xx_rate_pct']:.1f}%)")
    print(f"  Throughput:          {summary['rps']} requests/sec")
    print("-" * 78)
    print("  LATENCY DISTRIBUTION (Overall):")
    print(f"    Min:   {summary['min_ms']:>8.2f} ms      P50:  {summary['p50_ms']:>8.2f} ms")
    print(f"    Mean:  {summary['mean_ms']:>8.2f} ms      P90:  {summary['p90_ms']:>8.2f} ms")
    print(f"    Max:   {summary['max_ms']:>8.2f} ms      P95:  {summary['p95_ms']:>8.2f} ms")
    print(f"    Std:   {summary['stddev_ms']:>8.2f} ms      P99:  {summary['p99_ms']:>8.2f} ms")
    print("-" * 78)
    print("  ENDPOINT BREAKDOWN:")
    print(f"    /api/detect   ({detect['count']:>3} reqs): P50={detect['p50_ms']:>6.1f}ms | P95={detect['p95_ms']:>6.1f}ms | Mean Inf={detect.get('mean_inference_ms', 0):>5.1f}ms")
    print(f"    /api/distance ({distance['count']:>3} reqs): P50={distance['p50_ms']:>6.1f}ms | P95={distance['p95_ms']:>6.1f}ms | Mean={distance['mean_ms']:>5.1f}ms")
    print("-" * 78)
    print("  BOTTLENECK & HARDWARE PROFILING:")
    print(f"    Status:            {bottleneck['status']}")
    print(f"    Overall P95:       {bottleneck['overall_p95_ms']:.1f} ms (Target budget: < {bottleneck['target_p95_budget_ms']:.1f} ms)")
    print(f"    CPU Cores / Util:  {bottleneck['hardware_info']['logical_cores']} cores / {bottleneck['hardware_info']['cpu_utilization_pct']}% utilization")
    print(f"    Diagnosis:         {bottleneck['bottleneck_diagnosis']}")
    print("-" * 78)
    print("  MEMORY METRICS (psutil RSS):")
    print(f"    Baseline RSS:      {mem['baseline_rss_mb']:.1f} MB")
    print(f"    Peak RSS:          {mem['peak_rss_mb']:.1f} MB (+{mem['peak_delta_mb']:.1f} MB)")
    print(f"    Final RSS:         {mem['final_rss_mb']:.1f} MB (Delta: {mem['rss_delta_mb']:+.1f} MB)")
    print(f"    Leak Status:       {'NO LEAK DETECTED (STABLE)' if not mem['leak_detected'] else 'LEAK WARNING'}")
    print("=" * 78)
    print("  ACCEPTANCE CRITERIA VERIFICATION:")
    for key, val in criteria.items():
        if key == "overall_status":
            continue
        status_sym = "[PASS]" if val else "[FAIL]"
        print(f"    {status_sym} {key.replace('_', ' ').title()}")
    print("-" * 78)
    overall_sym = ">>> OVERALL STATUS: " + ("PASS" if criteria["overall_status"] == "PASS" else "FAIL") + " <<<"
    print(f"  {overall_sym}")
    print("=" * 78)
    print()


def run_pipeline(
    clients: int = 50,
    requests_count: int = 100,
    duration_sec: float = None,
    base_url: str = "http://127.0.0.1:5000",
    output_path: str = "stress_test_report.json",
    target_endpoint: str = "all",
    p95_budget_ms: float = 80.0
) -> Dict[str, Any]:
    """Execute complete stress test pipeline, generate report, and save JSON."""
    parsed_port = 5000
    try:
        from urllib.parse import urlparse
        u = urlparse(base_url)
        if u.port:
            parsed_port = u.port
    except Exception:
        pass

    server_instance = None
    if not is_port_in_use(parsed_port):
        print(f"[INFO] No active listener on port {parsed_port}. Launching multi-threaded WSGI server...")
        server_instance = start_inprocess_server(port=parsed_port)
        if not wait_for_server(base_url, timeout_sec=12.0):
            print(f"[ERROR] Failed to connect to server at {base_url} within 12 seconds.")
            sys.exit(1)
        print(f"[INFO] WSGI server running and healthy on {base_url}.")
    else:
        print(f"[INFO] Existing server detected on {base_url}. Verifying health...")
        if not wait_for_server(base_url, timeout_sec=5.0):
            print(f"[WARNING] Server on port {parsed_port} did not respond with 200 to /api/health. Proceeding...")

    print_banner(clients=clients, total_reqs=requests_count, target_url=base_url)

    # Initialize LatencyProfiler and MemoryTracker
    profiler = LatencyProfiler(target_p95_budget_ms=p95_budget_ms)
    memory_tracker = MemoryTracker(leak_threshold_mb=50.0)

    # Run memory tracking during concurrent execution
    print("[INFO] Starting real-time RSS memory tracking and concurrent load generator...")
    memory_tracker.start()

    runner = ConcurrentRunner(
        base_url=base_url,
        concurrency=clients,
        total_requests=requests_count,
        duration_sec=duration_sec,
        profiler=profiler,
        target_endpoint=target_endpoint,
        timeout_sec=30.0
    )

    try:
        runner.run()
    finally:
        memory_tracker.stop(cooldown_sec=0.5)

    # Compile reports
    latency_report = profiler.generate_report()
    memory_metrics = memory_tracker.get_metrics()
    bottleneck = latency_report["bottleneck_analysis"]
    summary = latency_report["overall"]

    # Evaluate Acceptance Criteria
    fifty_concurrent_tested = clients >= 50 and summary["count"] >= clients
    zero_5xx_errors = (summary["unhandled_5xx_count"] == 0) and (summary["unhandled_5xx_rate_pct"] == 0.0)
    p95_criteria_met = bottleneck["meets_budget"] or (bottleneck["status"] == "HARDWARE_CPU_BOUND" and bool(bottleneck["bottleneck_diagnosis"]))
    memory_leak_free = not memory_metrics["leak_detected"]

    all_criteria_met = (
        fifty_concurrent_tested and
        zero_5xx_errors and
        p95_criteria_met and
        memory_leak_free
    )

    full_report = {
        "test_metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "target_url": base_url,
            "concurrency_clients": clients,
            "total_requests": summary["count"],
            "target_endpoint": target_endpoint,
            "python_version": sys.version.split()[0],
            "os": f"{platform.system()} {platform.release()}",
            "cpu_model": get_cpu_brand_name(),
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False)
        },
        "acceptance_criteria": {
            "fifty_concurrent_clients_tested": fifty_concurrent_tested,
            "zero_unhandled_5xx_errors": zero_5xx_errors,
            "p95_budget_or_hardware_cpu_bottleneck_documented": p95_criteria_met,
            "memory_leak_free": memory_leak_free,
            "overall_status": "PASS" if all_criteria_met else "FAIL"
        },
        "summary": summary,
        "endpoints": latency_report["by_endpoint"],
        "bottleneck_profiling": bottleneck,
        "memory_metrics": memory_metrics
    }

    # Save structured JSON report
    out_file = Path(output_path)
    if not out_file.is_absolute():
        out_file = PROJECT_ROOT / output_path

    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2)
        print(f"[INFO] Stress test report saved to: {out_file.resolve()}")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON report to {out_file}: {e}")

    # Output Console Summary
    print_console_summary(full_report)

    if server_instance is not None and hasattr(server_instance, "shutdown"):
        try:
            server_instance.shutdown()
        except Exception:
            pass

    return full_report


def main():
    parser = argparse.ArgumentParser(description="YOLO Object Distance System Stress Testing Pipeline")
    parser.add_argument("--clients", "-c", type=int, default=50, help="Number of concurrent virtual clients (default: 50)")
    parser.add_argument("--requests", "-n", type=int, default=100, help="Total number of requests to execute (default: 100)")
    parser.add_argument("--duration", "-d", type=float, default=None, help="Sustained test duration in seconds (optional)")
    parser.add_argument("--url", "-u", type=str, default="http://127.0.0.1:5000", help="Base URL of target API (default: http://127.0.0.1:5000)")
    parser.add_argument("--output", "-o", type=str, default="stress_test_report.json", help="Path for JSON report output (default: stress_test_report.json)")
    parser.add_argument("--target", "-t", type=str, default="all", choices=["all", "detect", "distance"], help="Endpoints to target (default: all)")
    parser.add_argument("--p95-budget", type=float, default=80.0, help="Target P95 latency budget in ms (default: 80.0)")

    args = parser.parse_args()

    report = run_pipeline(
        clients=args.clients,
        requests_count=args.requests,
        duration_sec=args.duration,
        base_url=args.url,
        output_path=args.output,
        target_endpoint=args.target,
        p95_budget_ms=args.p95_budget
    )

    if report["acceptance_criteria"]["overall_status"] != "PASS":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
