import os
import time
import threading
from typing import Dict, List, Optional, Any
import psutil


class MemoryTracker:
    """
    Monitors RSS and VMS memory usage using psutil before, during, and after sustained load.
    Calculates memory delta, peak usage, and detects memory leaks via slope analysis.
    """

    def __init__(self, target_pid: Optional[int] = None, sample_interval_sec: float = 0.25, leak_threshold_mb: float = 50.0):
        self.target_pid = target_pid or os.getpid()
        self.sample_interval_sec = sample_interval_sec
        self.leak_threshold_mb = leak_threshold_mb
        
        try:
            self.process = psutil.Process(self.target_pid)
        except psutil.NoSuchProcess:
            self.process = psutil.Process(os.getpid())
            self.target_pid = self.process.pid

        self.samples: List[Dict[str, Any]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        self.baseline_rss_mb: float = 0.0
        self.baseline_vms_mb: float = 0.0
        self.peak_rss_mb: float = 0.0
        self.final_rss_mb: float = 0.0

    def _sample_current(self) -> Dict[str, Any]:
        """Fetch current RSS, VMS, and memory percent for target and any child processes."""
        try:
            total_rss = 0
            total_vms = 0
            
            # Target process
            mem = self.process.memory_info()
            total_rss += mem.rss
            total_vms += mem.vms

            # Include child processes if running multi-process server
            try:
                for child in self.process.children(recursive=True):
                    try:
                        cmem = child.memory_info()
                        total_rss += cmem.rss
                        total_vms += cmem.vms
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            rss_mb = round(total_rss / (1024 * 1024), 2)
            vms_mb = round(total_vms / (1024 * 1024), 2)
            mem_pct = round(self.process.memory_percent(), 2)

            return {
                "timestamp": time.time(),
                "rss_mb": rss_mb,
                "vms_mb": vms_mb,
                "percent": mem_pct
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "timestamp": time.time(),
                "rss_mb": self.baseline_rss_mb,
                "vms_mb": self.baseline_vms_mb,
                "percent": 0.0
            }

    def _monitor_loop(self):
        """Background sampling loop."""
        while not self._stop_event.is_set():
            sample = self._sample_current()
            if self.start_time:
                sample["elapsed_sec"] = round(sample["timestamp"] - self.start_time, 2)
            else:
                sample["elapsed_sec"] = 0.0
            self.samples.append(sample)
            self._stop_event.wait(self.sample_interval_sec)

    def start(self):
        """Start tracking: records baseline and launches periodic background sampler."""
        self.start_time = time.time()
        self.samples.clear()
        self._stop_event.clear()

        initial_sample = self._sample_current()
        initial_sample["elapsed_sec"] = 0.0
        self.samples.append(initial_sample)

        self.baseline_rss_mb = initial_sample["rss_mb"]
        self.baseline_vms_mb = initial_sample["vms_mb"]
        self.peak_rss_mb = self.baseline_rss_mb

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self, cooldown_sec: float = 0.5):
        """Stop tracking: allows cooldown, records final memory state."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        if cooldown_sec > 0:
            time.sleep(cooldown_sec)

        self.end_time = time.time()
        final_sample = self._sample_current()
        final_sample["elapsed_sec"] = round(final_sample["timestamp"] - (self.start_time or final_sample["timestamp"]), 2)
        self.samples.append(final_sample)

        self.final_rss_mb = final_sample["rss_mb"]
        all_rss = [s["rss_mb"] for s in self.samples]
        self.peak_rss_mb = max(all_rss) if all_rss else self.final_rss_mb

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def compute_slope(self) -> float:
        """
        Calculate linear regression slope of RSS (MB/s).
        A positive slope sustained across long tests indicates memory accumulation.
        """
        if len(self.samples) < 3:
            return 0.0

        ts = [s.get("elapsed_sec", 0.0) for s in self.samples]
        ys = [s["rss_mb"] for s in self.samples]

        n = len(ts)
        mean_t = sum(ts) / n
        mean_y = sum(ys) / n

        denom = sum((t - mean_t) ** 2 for t in ts)
        if denom == 0:
            return 0.0

        numer = sum((t - mean_t) * (y - mean_y) for t, y in zip(ts, ys))
        return round(numer / denom, 4)

    def get_metrics(self) -> Dict[str, Any]:
        """Produce structured memory utilization and leak detection report."""
        rss_delta = round(self.final_rss_mb - self.baseline_rss_mb, 2)
        peak_delta = round(self.peak_rss_mb - self.baseline_rss_mb, 2)
        slope = self.compute_slope()

        # Leak criterion: permanent retained RSS exceeds threshold AND positive slope
        leak_detected = (rss_delta > self.leak_threshold_mb) and (slope > 0.5)

        if leak_detected:
            stability_status = "MEMORY_LEAK_DETECTED"
            summary_msg = f"Potential memory leak detected: sustained RSS growth of +{rss_delta:.1f}MB (slope {slope:+.3f} MB/s)."
        else:
            stability_status = "STABLE"
            summary_msg = f"Memory utilization is stable: baseline {self.baseline_rss_mb:.1f}MB, peak {self.peak_rss_mb:.1f}MB, delta {rss_delta:+.1f}MB (no memory leaks detected)."

        return {
            "status": stability_status,
            "target_pid": self.target_pid,
            "baseline_rss_mb": self.baseline_rss_mb,
            "peak_rss_mb": self.peak_rss_mb,
            "final_rss_mb": self.final_rss_mb,
            "rss_delta_mb": rss_delta,
            "peak_delta_mb": peak_delta,
            "leak_threshold_mb": self.leak_threshold_mb,
            "rss_slope_mb_per_sec": slope,
            "leak_detected": leak_detected,
            "sample_count": len(self.samples),
            "summary": summary_msg,
            "recent_samples": self.samples[-10:] if len(self.samples) > 10 else self.samples
        }
