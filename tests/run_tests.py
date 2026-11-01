#!/usr/bin/env python3
"""Integration and Edge-Case Test Suite Runner for YOLO Object Distance System.

Executes all unit, integration, and edge-case test modules in tests/:
- tests/test_unit_detector.py
- tests/test_unit_distance.py
- tests/test_unit_image_utils.py
- tests/test_api_endpoints.py
- tests/test_edge_cases.py

Usage:
    python tests/run_tests.py [--verbose] [--report-file PATH]
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

MODULE_SPECS = [
    ("test_unit_detector", "Unit Tests: YOLO Detector"),
    ("test_unit_distance", "Unit Tests: Distance Estimator"),
    ("test_unit_image_utils", "Unit Tests: Image Utilities"),
    ("test_api_endpoints", "Integration Tests: API Endpoints"),
    ("test_edge_cases", "Edge-Case Tests: Robustness & Boundaries")
]


class PytestCollectorPlugin:
    """Pytest plugin to collect structured test results across test suites."""

    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            status = "PASSED" if report.passed else ("FAILED" if report.failed else "SKIPPED")
            name = report.location[2] if report.location else report.nodeid
            self.results.append({
                "nodeid": report.nodeid,
                "name": name,
                "status": status,
                "duration_ms": round(report.duration * 1000, 2),
                "error": str(report.longrepr) if report.failed else None
            })
        elif report.failed and report.when in ("setup", "teardown"):
            name = report.location[2] if report.location else report.nodeid
            self.results.append({
                "nodeid": report.nodeid,
                "name": f"{name} ({report.when})",
                "status": "FAILED",
                "duration_ms": round(report.duration * 1000, 2),
                "error": str(report.longrepr)
            })

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = time.time()


def run_tests(verbose=True, report_file=None):
    """Execute all tests in tests/ via pytest and format structured results."""
    collector = PytestCollectorPlugin()

    pytest_args = [
        str(TESTS_DIR),
        "-v" if verbose else "-q",
        "--tb=short"
    ]

    print("\n" + "=" * 80)
    print("  YOLO OBJECT DISTANCE SYSTEM — INTEGRATION & EDGE-CASE TEST SUITE")
    print("=" * 80 + "\n")

    start_time = time.time()
    exit_code = pytest.main(pytest_args, plugins=[collector])
    total_duration_ms = round((time.time() - start_time) * 1000, 2)

    # Organize collected results by module
    module_results = []
    total_passed = 0
    total_failed = 0

    print("\n" + "=" * 80)
    print("  DETAILED TEST MODULE BREAKDOWN")
    print("=" * 80)

    for mod_key, mod_title in MODULE_SPECS:
        mod_tests = [r for r in collector.results if mod_key in r["nodeid"]]
        mod_passed = sum(1 for r in mod_tests if r["status"] == "PASSED")
        mod_failed = sum(1 for r in mod_tests if r["status"] != "PASSED")
        total_passed += mod_passed
        total_failed += mod_failed

        module_results.append({
            "title": mod_title,
            "passed": mod_passed,
            "failed": mod_failed,
            "total": len(mod_tests),
            "tests": mod_tests
        })

        print(f"\n--- {mod_title} ---")
        for t in mod_tests:
            icon = "[PASS]" if t["status"] == "PASSED" else "[FAIL]"
            print(f"  {icon} {t['nodeid']} ({t['duration_ms']} ms)")
            if t["error"]:
                print(f"         Error: {t['error']}")
        print(f"  Module Summary: {mod_passed}/{len(mod_tests)} passed")

    total_tests = len(collector.results)
    pass_rate = (total_passed / total_tests * 100.0) if total_tests > 0 else 0.0

    print("\n" + "=" * 80)
    print(f"  FINAL SUMMARY: {total_passed}/{total_tests} tests passed ({pass_rate:.1f}%)")
    print(f"  Total Duration: {total_duration_ms} ms")
    print("=" * 80 + "\n")

    summary = {
        "total_passed": total_passed,
        "total_failed": total_failed,
        "total_tests": total_tests,
        "total_duration_ms": total_duration_ms,
        "pass_rate_pct": round(pass_rate, 2),
        "modules": module_results
    }

    if report_file:
        report_path = Path(report_file)
        if not report_path.is_absolute():
            report_path = PROJECT_ROOT / report_file
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[REPORT] Saved test results to {report_path}")

    return summary, exit_code


def main():
    parser = argparse.ArgumentParser(description="Run YOLO Object Distance System test suite.")
    parser.add_argument("--verbose", action="store_true", default=True, help="Print verbose test results")
    parser.add_argument("--report-file", type=str, default=None, help="Save JSON test report to file")
    args = parser.parse_args()

    summary, exit_code = run_tests(verbose=args.verbose, report_file=args.report_file)
    sys.exit(0 if (summary["total_failed"] == 0 and exit_code == 0) else 1)


if __name__ == "__main__":
    main()
