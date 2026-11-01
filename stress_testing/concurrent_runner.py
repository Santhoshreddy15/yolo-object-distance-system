import asyncio
import base64
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import httpx

from stress_testing.latency_profiler import LatencyProfiler

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_IMAGE_PATH = PROJECT_ROOT / "backend" / "sample_images" / "traffic_urban.jpg"


def get_test_image_base64() -> str:
    """Load or generate a realistic base64 JPEG image payload."""
    if SAMPLE_IMAGE_PATH.is_file():
        try:
            with open(SAMPLE_IMAGE_PATH, "rb") as f:
                raw_bytes = f.read()
            return "data:image/jpeg;base64," + base64.b64encode(raw_bytes).decode("utf-8")
        except Exception:
            pass

    # Fallback synthetic 320x240 image
    import cv2
    import numpy as np
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 60), (150, 180), (0, 255, 0), -1)
    cv2.rectangle(img, (180, 80), (280, 200), (255, 0, 0), -1)
    _, buf = cv2.imencode(".jpg", img)
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")


def get_test_distance_payload() -> Dict[str, Any]:
    """Generate realistic payload for POST /api/distance."""
    return {
        "object_a": {
            "class_name": "car",
            "class": "car",
            "height": 140,
            "width": 220,
            "center": [270, 430],
            "bbox": [160, 360, 380, 500]
        },
        "object_b": {
            "class_name": "person",
            "class": "person",
            "height": 180,
            "width": 80,
            "center": [680, 390],
            "bbox": [640, 300, 720, 480]
        },
        "image_dimensions": {"width": 960, "height": 600},
        "focal_length_px": 864.0
    }


class ConcurrentRunner:
    """
    Async concurrent client runner simulating 50+ simultaneous virtual clients
    generating sustained traffic targeting /api/detect and /api/distance.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:5000",
        concurrency: int = 50,
        total_requests: int = 100,
        duration_sec: Optional[float] = None,
        profiler: Optional[LatencyProfiler] = None,
        target_endpoint: str = "all", # 'all', 'detect', 'distance'
        timeout_sec: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.concurrency = max(1, int(concurrency))
        self.total_requests = max(self.concurrency, int(total_requests))
        self.duration_sec = duration_sec
        self.profiler = profiler or LatencyProfiler()
        self.target_endpoint = target_endpoint.lower()
        self.timeout_sec = float(timeout_sec)

        self._test_img_b64: Optional[str] = None
        self._distance_payload: Optional[Dict[str, Any]] = None

    def _prepare_payloads(self):
        if self._test_img_b64 is None:
            self._test_img_b64 = get_test_image_base64()
        if self._distance_payload is None:
            self._distance_payload = get_test_distance_payload()

    async def _send_detect_request(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        url = f"{self.base_url}/api/detect"
        payload = {
            "image_base64": self._test_img_b64,
            "conf": 0.25,
            "iou": 0.45
        }
        t0 = time.time()
        inference_time_ms = None
        status = 0
        err_msg = None

        try:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            latency_ms = (time.time() - t0) * 1000.0
            status = resp.status_code
            if resp.status_code == 200:
                data = resp.json()
                inference_time_ms = data.get("inference_time_ms")
            else:
                err_msg = f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            latency_ms = (time.time() - t0) * 1000.0
            status = 599
            err_msg = str(e)

        self.profiler.record(
            endpoint="/api/detect",
            latency_ms=latency_ms,
            status_code=status,
            inference_time_ms=inference_time_ms,
            error=err_msg
        )
        return {"endpoint": "/api/detect", "status": status, "latency_ms": latency_ms, "error": err_msg}

    async def _send_distance_request(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        url = f"{self.base_url}/api/distance"
        t0 = time.time()
        status = 0
        err_msg = None

        try:
            resp = await client.post(url, json=self._distance_payload, headers={"Content-Type": "application/json"})
            latency_ms = (time.time() - t0) * 1000.0
            status = resp.status_code
            if resp.status_code != 200:
                err_msg = f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            latency_ms = (time.time() - t0) * 1000.0
            status = 599
            err_msg = str(e)

        self.profiler.record(
            endpoint="/api/distance",
            latency_ms=latency_ms,
            status_code=status,
            inference_time_ms=None,
            error=err_msg
        )
        return {"endpoint": "/api/distance", "status": status, "latency_ms": latency_ms, "error": err_msg}

    async def _worker(self, worker_id: int, client: httpx.AsyncClient, queue: asyncio.Queue, results: List[Dict[str, Any]]):
        while True:
            try:
                task_endpoint = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            if task_endpoint == "detect":
                res = await self._send_detect_request(client)
            else:
                res = await self._send_distance_request(client)
            results.append(res)
            queue.task_done()

    async def _worker_duration_mode(
        self,
        worker_id: int,
        client: httpx.AsyncClient,
        end_deadline: float,
        results: List[Dict[str, Any]]
    ):
        counter = worker_id
        while time.time() < end_deadline:
            if self.target_endpoint == "detect":
                res = await self._send_detect_request(client)
            elif self.target_endpoint == "distance":
                res = await self._send_distance_request(client)
            else:
                # Alternate between detect and distance
                if counter % 2 == 0:
                    res = await self._send_detect_request(client)
                else:
                    res = await self._send_distance_request(client)
            results.append(res)
            counter += 1
            # Small yield to event loop
            await asyncio.sleep(0.001)

    async def run_async(self) -> Dict[str, Any]:
        """Execute concurrent load testing run."""
        self._prepare_payloads()
        self.profiler.start()

        limits = httpx.Limits(
            max_connections=max(100, self.concurrency * 2),
            max_keepalive_connections=max(50, self.concurrency)
        )
        timeout = httpx.Timeout(
            connect=10.0,
            read=self.timeout_sec,
            write=10.0,
            pool=10.0
        )

        results: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            if self.duration_sec and self.duration_sec > 0:
                # Sustained duration mode
                deadline = time.time() + self.duration_sec
                tasks = [
                    asyncio.create_task(self._worker_duration_mode(i, client, deadline, results))
                    for i in range(self.concurrency)
                ]
                await asyncio.gather(*tasks)
            else:
                # Fixed total requests batch mode
                queue: asyncio.Queue[str] = asyncio.Queue()
                for i in range(self.total_requests):
                    if self.target_endpoint == "detect":
                        queue.put_nowait("detect")
                    elif self.target_endpoint == "distance":
                        queue.put_nowait("distance")
                    else:
                        # 50% detect, 50% distance
                        queue.put_nowait("detect" if i % 2 == 0 else "distance")

                tasks = [
                    asyncio.create_task(self._worker(i, client, queue, results))
                    for i in range(self.concurrency)
                ]
                await asyncio.gather(*tasks)

        self.profiler.stop()
        return self.profiler.generate_report()

    def run(self) -> Dict[str, Any]:
        """Synchronous entry point that runs the async event loop."""
        return asyncio.run(self.run_async())
