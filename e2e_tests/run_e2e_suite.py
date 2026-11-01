#!/usr/bin/env python3
"""E2E Test Suite Runner for YOLO Object Detection & Distance Measurement System.

Executes all 4 test tiers:
- Tier 1: Feature Coverage (GET /, GET /api/health, POST /api/detect, POST /api/distance)
- Tier 2: Boundary & Corner Cases (0-byte, corrupt headers, oversized payloads, div-by-zero, negative coords)
- Tier 3: Cross-Feature Combinations (pairwise detect->distance, multiple classes, format invariance)
- Tier 4: Real-World Workloads (traffic scene, warehouse forklift, calibrated scene accuracy)

Usage:
    python e2e_tests/run_e2e_suite.py [--all] [--tier {1,2,3,4}] [--verbose] [--report-file PATH]
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
E2E_DIR = PROJECT_ROOT / "e2e_tests"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

TIER_FILES = {
    1: ("Tier 1: Feature Coverage", "test_tier1_features.py"),
    2: ("Tier 2: Boundary & Corner Cases", "test_tier2_boundaries.py"),
    3: ("Tier 3: Cross-Feature Combinations", "test_tier3_combinations.py"),
    4: ("Tier 4: Real-World Scenarios", "test_tier4_workloads.py")
}


class E2ECollectorPlugin:
    """Pytest plugin to collect structured E2E test results by tier."""

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
                "status": "ERROR",
                "duration_ms": round(report.duration * 1000, 2),
                "error": str(report.longrepr)
            })

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = time.time()


def run_e2e_suite(tiers=None, verbose=False, report_file="e2e_test_report.json"):
    """Execute E2E test suite across specified tiers via pytest."""
    if tiers is None:
        tiers = [1, 2, 3, 4]

    target_files = []
    for t in tiers:
        if t in TIER_FILES:
            target_files.append(str(E2E_DIR / TIER_FILES[t][1]))

    collector = E2ECollectorPlugin()
    pytest_args = target_files + [
        "-v" if verbose else "-q",
        "--tb=short"
    ]

    start_time = time.time()
    exit_code = pytest.main(pytest_args, plugins=[collector])
    total_duration_ms = round((time.time() - start_time) * 1000, 2)

    # Organize results by tier
    tier_summaries = []
    for t in tiers:
        tier_title, filename = TIER_FILES[t]
        file_stem = Path(filename).stem
        tier_tests = [r for r in collector.results if file_stem in r["nodeid"]]

        passed = sum(1 for r in tier_tests if r["status"] == "PASSED")
        failed = sum(1 for r in tier_tests if r["status"] == "FAILED")
        errors = sum(1 for r in tier_tests if r["status"] == "ERROR")
        total = len(tier_tests)
        pass_rate = (passed / total * 100.0) if total > 0 else 0.0

        tier_summaries.append({
            "tier": t,
            "title": tier_title,
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate_pct": round(pass_rate, 2),
            "tests": tier_tests
        })

    total_tests = sum(t["total"] for t in tier_summaries)
    total_passed = sum(t["passed"] for t in tier_summaries)
    total_failed = sum(t["failed"] for t in tier_summaries)
    total_errors = sum(t["errors"] for t in tier_summaries)
    overall_pass_rate = (total_passed / total_tests * 100.0) if total_tests > 0 else 0.0

    report = {
        "project": "YOLO Object Detection & Distance Measurement System",
        "suite": "Opaque-Box E2E Test Suite",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_ms": total_duration_ms,
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_failed,
        "errors": total_errors,
        "overall_pass_rate_pct": round(overall_pass_rate, 2),
        "tier_breakdown": tier_summaries
    }

    _print_report_table(report)

    if report_file:
        report_path = Path(report_file)
        if not report_path.is_absolute():
            report_path = PROJECT_ROOT / report_file
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"[INFO] Full structured report saved to: {report_path}")

    return report, exit_code


def _print_report_table(report):
    """Format and print ASCII summary table."""
    border = "=" * 80
    divider = "-" * 80

    print("\n" + border)
    print("          YOLO OBJECT DETECTION & DISTANCE SYSTEM — E2E TEST REPORT")
    print(border)
    print(f"{'Tier':<35} {'Total':>7} {'Passed':>8} {'Failed':>8} {'Errors':>8} {'Pass %':>8}")
    print(divider)

    for t in report["tier_breakdown"]:
        print(f"{t['title']:<35} {t['total']:>7} {t['passed']:>8} {t['failed']:>8} {t['errors']:>8} {t['pass_rate_pct']:>7.1f}%")

    print(divider)
    print(f"{'TOTAL / OVERALL':<35} {report['total_tests']:>7} {report['passed']:>8} {report['failed']:>8} {report['errors']:>8} {report['overall_pass_rate_pct']:>7.1f}%")
    print(border)
    print(f"Total Execution Time: {report['duration_ms']} ms")
    if report["failed"] > 0 or report["errors"] > 0:
        print("\n[FAILURES / DEFECTS DETECTED]")
        for t in report["tier_breakdown"]:
            for test in t["tests"]:
                if test["status"] != "PASSED":
                    print(f"  • {test['name']} ({t['title']}): {test['error']}")
    print(border + "\n")


def main():
    parser = argparse.ArgumentParser(description="YOLO Object Distance System E2E Suite Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run a specific tier (1, 2, 3, or 4)")
    parser.add_argument("--all", action="store_true", default=True, help="Run all test tiers (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed test outputs")
    parser.add_argument("--report-file", type=str, default="e2e_test_report.json", help="Path to save JSON report")

    args = parser.parse_args()

    tiers = [args.tier] if args.tier else [1, 2, 3, 4]
    report, exit_code = run_e2e_suite(tiers=tiers, verbose=args.verbose, report_file=args.report_file)

    sys.exit(0 if (report["failed"] == 0 and report["errors"] == 0 and exit_code == 0) else 1)


if __name__ == "__main__":
    main()
