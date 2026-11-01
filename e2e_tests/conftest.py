import os
import sys
import io
import base64
from pathlib import Path
import pytest
import numpy as np
import cv2

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.config import Config


class E2ETestConfig(Config):
    """Test configuration for E2E opaque-box testing."""
    TESTING = True
    DEBUG = False


def create_synthetic_image(format_ext="JPEG", width=640, height=480, draw_objects=True) -> bytes:
    """Generate in-memory synthetic image bytes with optional vehicle/person shapes."""
    canvas = np.full((height, width, 3), (40, 40, 40), dtype=np.uint8)

    if draw_objects:
        # Sky/Horizon
        horizon = int(height * 0.4)
        canvas[:horizon, :] = (180, 130, 90) # muted sky

        # Road
        road_pts = np.array([
            [0, height],
            [width, height],
            [int(width * 0.65), horizon],
            [int(width * 0.35), horizon]
        ], np.int32)
        cv2.fillPoly(canvas, [road_pts], (60, 60, 60))

        # Lane markings
        cv2.line(canvas, (int(width * 0.5), horizon), (int(width * 0.5), height), (220, 220, 220), 3)

        # Vehicle A (Car - red)
        c1_x, c1_y, c1_w, c1_h = int(width * 0.15), int(height * 0.55), int(width * 0.25), int(height * 0.2)
        cv2.rectangle(canvas, (c1_x, c1_y), (c1_x + c1_w, c1_y + c1_h), (30, 40, 180), -1)
        cv2.circle(canvas, (c1_x + 30, c1_y + c1_h), 14, (15, 15, 15), -1)
        cv2.circle(canvas, (c1_x + c1_w - 30, c1_y + c1_h), 14, (15, 15, 15), -1)

        # Vehicle B (Car - blue)
        c2_x, c2_y, c2_w, c2_h = int(width * 0.6), int(height * 0.5), int(width * 0.2), int(height * 0.16)
        cv2.rectangle(canvas, (c2_x, c2_y), (c2_x + c2_w, c2_y + c2_h), (180, 120, 20), -1)
        cv2.circle(canvas, (c2_x + 24, c2_y + c2_h), 11, (15, 15, 15), -1)
        cv2.circle(canvas, (c2_x + c2_w - 24, c2_y + c2_h), 11, (15, 15, 15), -1)

    ext = format_ext.upper()
    if ext in ("JPG", "JPEG"):
        success, buffer = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    elif ext == "PNG":
        success, buffer = cv2.imencode(".png", canvas)
    elif ext == "WEBP":
        success, buffer = cv2.imencode(".webp", canvas)
    else:
        success, buffer = cv2.imencode(".jpg", canvas)

    if not success:
        raise ValueError(f"Failed to encode synthetic image to {format_ext}")

    return buffer.tobytes()


@pytest.fixture(scope="session")
def app():
    """Create Flask application fixture for testing."""
    application = create_app(config_class=E2ETestConfig)
    return application


@pytest.fixture(scope="session")
def client(app):
    """Create Flask test client fixture."""
    return app.test_client()


@pytest.fixture
def sample_jpeg_bytes():
    """Valid JPEG image bytes."""
    return create_synthetic_image("JPEG", 640, 480)


@pytest.fixture
def sample_png_bytes():
    """Valid PNG image bytes."""
    return create_synthetic_image("PNG", 640, 480)


@pytest.fixture
def sample_webp_bytes():
    """Valid WEBP image bytes."""
    return create_synthetic_image("WEBP", 640, 480)


@pytest.fixture
def sample_raw_base64(sample_jpeg_bytes):
    """Raw base64 string without data URI prefix."""
    return base64.b64encode(sample_jpeg_bytes).decode("utf-8")


@pytest.fixture
def sample_base64_data_url(sample_raw_base64):
    """Data URI formatted base64 string."""
    return f"data:image/jpeg;base64,{sample_raw_base64}"


@pytest.fixture
def sample_corrupt_bytes():
    """Invalid non-image byte sequence."""
    return b"\x00\x01\x02\x03\x04INVALID_CORRUPTED_IMAGE_HEADER_1234567890\xff\xfe"


@pytest.fixture
def sample_zero_bytes():
    """Zero-byte empty payload."""
    return b""


@pytest.fixture
def synthetic_car_pair():
    """Calibrated pair of vehicles matching project standard test scene."""
    return {
        "object_a": {
            "id": "car_lead",
            "class_name": "car",
            "class": "car",
            "height": 140,
            "width": 260,
            "center": [270.0, 430.0],
            "bbox": [140, 360, 400, 500]
        },
        "object_b": {
            "id": "car_trail",
            "class_name": "car",
            "class": "car",
            "height": 110,
            "width": 210,
            "center": [685.0, 365.0],
            "bbox": [580, 310, 790, 420]
        },
        "image_dimensions": {"width": 960, "height": 600},
        "focal_length_px": 864.0
    }


@pytest.fixture
def synthetic_forklift_pair():
    """Industrial warehouse scenario: Forklift and Pedestrian worker."""
    return {
        "object_a": {
            "id": "forklift_unit_1",
            "class_name": "forklift",
            "class": "forklift",
            "height": 220,
            "width": 180,
            "center": [320.0, 360.0],
            "bbox": [230, 250, 410, 470]
        },
        "object_b": {
            "id": "worker_pedestrian_1",
            "class_name": "person",
            "class": "person",
            "height": 280,
            "width": 70,
            "center": [580.0, 380.0],
            "bbox": [545, 240, 615, 520]
        },
        "image_dimensions": {"width": 1280, "height": 720},
        "focal_length_px": 920.0
    }


@pytest.fixture
def optical_bench_calibrated_pair():
    """Ground truth optical calibration bench targets (Z_A = 5.0m, Z_B = 10.0m)."""
    f = 800.0
    h_real = 1.00 # 1 meter height target
    # h_pixel = (f * H_real) / Z
    h_px_a = (f * h_real) / 5.0  # 160 px
    h_px_b = (f * h_real) / 10.0 # 80 px
    return {
        "object_a": {
            "id": "target_5m",
            "class_name": "target",
            "class": "target",
            "height": h_px_a,
            "width": 100,
            "center": [500.0, 400.0],
            "bbox": [450, 400 - int(h_px_a / 2), 550, 400 + int(h_px_a / 2)]
        },
        "object_b": {
            "id": "target_10m",
            "class_name": "target",
            "class": "target",
            "height": h_px_b,
            "width": 50,
            "center": [500.0, 300.0],
            "bbox": [475, 300 - int(h_px_b / 2), 525, 300 + int(h_px_b / 2)]
        },
        "image_dimensions": {"width": 1000, "height": 800},
        "focal_length_px": f,
        "ground_truth_z_a": 5.0,
        "ground_truth_z_b": 10.0,
        "ground_truth_distance_3d": 5.099 # sqrt((0)^2 + (-0.125 - (-0.25))^2 + (10 - 5)^2)
    }
