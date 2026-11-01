"""Tier 2: Boundary & Corner Cases E2E Tests.

Validates system resilience under stress, edge conditions, and adversarial inputs:
- Feature 1: Detection Boundaries (0-byte file, empty string, corrupt base64, corrupt image bytes, unsupported extensions, 1x1 image, solid black image)
- Feature 2: Distance Boundaries (missing object_a/b, empty JSON, height=0 division prevention, negative coords, extreme aspect ratios, focal=0, unknown classes)
- Feature 3: Protocol & Payload Boundaries (Content-Length >16MB, malformed JSON, boundary conf thresholds)

Each category contains at least 5 distinct test cases.
"""

import io
import base64
import numpy as np
import cv2
import pytest


# ==============================================================================
# Feature 1: Detection Boundaries (8 Test Cases)
# ==============================================================================

def test_tier2_detect_zero_byte_multipart_file(client):
    """B1.1: 0-byte file upload must be rejected with HTTP 400 Bad Request, not 500."""
    data = {"image": (io.BytesIO(b""), "empty.jpg")}
    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 400, (
        f"0-byte file should return 400 Bad Request, got {response.status_code}: {response.data}"
    )
    body = response.get_json()
    assert body is not None and "error" in body


def test_tier2_detect_empty_base64_string(client):
    """B1.2: Empty image_base64 string in JSON returns HTTP 400 Bad Request."""
    response = client.post("/api/detect", json={"image_base64": ""})
    assert response.status_code == 400, (
        f"Empty base64 string should return 400, got {response.status_code}: {response.data}"
    )


def test_tier2_detect_corrupt_base64_string(client):
    """B1.3: Corrupt/invalid base64 payload returns HTTP 400 Bad Request, not 500."""
    response = client.post("/api/detect", json={"image_base64": "!!!corrupted_base64_non_ascii$$$"})
    assert response.status_code == 400, (
        f"Corrupt base64 should return 400 Bad Request, got {response.status_code}: {response.data}"
    )


def test_tier2_detect_valid_base64_corrupt_image_data(client):
    """B1.4: Base64 string that encodes non-image garbage returns HTTP 400 Bad Request."""
    garbage_bytes = b"THIS_IS_NOT_AN_IMAGE_FILE_RANDOM_GARBAGE_PAYLOAD_1234567890"
    b64_garbage = base64.b64encode(garbage_bytes).decode("utf-8")
    response = client.post("/api/detect", json={"image_base64": b64_garbage})
    assert response.status_code == 400, (
        f"Non-image base64 bytes should return 400 Bad Request, got {response.status_code}: {response.data}"
    )
    body = response.get_json()
    assert body is not None and "error" in body


def test_tier2_detect_unsupported_file_extension(client, sample_jpeg_bytes):
    """B1.5: Unsupported file extensions (e.g. .exe, .sh, .txt) return 400 Bad Request."""
    for ext in ["dangerous.exe", "script.sh", "notes.txt", "archive.zip"]:
        data = {"image": (io.BytesIO(sample_jpeg_bytes), ext)}
        response = client.post("/api/detect", data=data, content_type="multipart/form-data")
        assert response.status_code == 400, (
            f"Extension {ext} should return 400 Bad Request, got {response.status_code}"
        )
        body = response.get_json()
        assert "error" in body and "Unsupported file extension" in body["error"]


def test_tier2_detect_missing_image_payload(client):
    """B1.6: POST request with empty payload returns HTTP 400 Bad Request."""
    response = client.post("/api/detect", json={})
    assert response.status_code == 400, (
        f"Empty payload must return 400, got {response.status_code}: {response.data}"
    )
    body = response.get_json()
    assert "error" in body


def test_tier2_detect_solid_black_zero_objects(client):
    """B1.7: Solid black canvas (zero objects) executes cleanly without server errors."""
    black_canvas = np.zeros((300, 300, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", black_canvas)
    data = {"image": (io.BytesIO(buffer.tobytes()), "black.jpg")}

    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 200, f"Solid black image should succeed with 200, got {response.status_code}"
    body = response.get_json()
    assert body.get("success") is True
    assert isinstance(body.get("detections"), list)


def test_tier2_detect_extreme_resolution_tiny(client):
    """B1.8: Extremely small 1x1 image handles gracefully without crashes."""
    tiny_canvas = np.full((1, 1, 3), 128, dtype=np.uint8)
    _, buffer = cv2.imencode(".png", tiny_canvas)
    data = {"image": (io.BytesIO(buffer.tobytes()), "tiny_1x1.png")}

    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 200, f"1x1 image should succeed or return valid response, got {response.status_code}"
    body = response.get_json()
    assert body.get("success") is True


# ==============================================================================
# Feature 2: Distance Estimation Boundaries (10 Test Cases)
# ==============================================================================

def test_tier2_distance_missing_object_a(client, synthetic_car_pair):
    """B2.1: Request missing object_a returns HTTP 400 Bad Request."""
    payload = dict(synthetic_car_pair)
    del payload["object_a"]
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 400, (
        f"Missing object_a must return 400, got {response.status_code}"
    )
    body = response.get_json()
    assert "error" in body


def test_tier2_distance_missing_object_b(client, synthetic_car_pair):
    """B2.2: Request missing object_b returns HTTP 400 Bad Request."""
    payload = dict(synthetic_car_pair)
    del payload["object_b"]
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 400, (
        f"Missing object_b must return 400, got {response.status_code}"
    )


def test_tier2_distance_empty_request_body(client):
    """B2.3: Empty request body to distance endpoint returns HTTP 400 Bad Request."""
    response = client.post("/api/distance", json={})
    assert response.status_code == 400, (
        f"Empty JSON body must return 400, got {response.status_code}"
    )


def test_tier2_distance_zero_height_bounding_box(client, synthetic_car_pair):
    """B2.4: Zero-height bounding box (height: 0) does not cause ZeroDivisionError."""
    payload = dict(synthetic_car_pair)
    payload["object_a"] = dict(synthetic_car_pair["object_a"])
    payload["object_a"]["height"] = 0

    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200, (
        f"height: 0 should be guarded (clamped to max(1, h)), got {response.status_code}"
    )
    data = response.get_json()
    assert data.get("success") is True
    # Clamped height to 1 yields finite depth Z
    assert data["object_a"]["estimated_depth_z"] > 0


def test_tier2_distance_negative_coordinates(client, synthetic_car_pair):
    """B2.5: Negative coordinates or centers outside image bounds do not crash the engine."""
    payload = dict(synthetic_car_pair)
    payload["object_a"] = {
        "id": "neg_obj",
        "class_name": "car",
        "height": 100,
        "width": 100,
        "center": [-50.0, -20.0],
        "bbox": [-100, -70, 0, 30]
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True
    assert data["metrics"]["estimated_relative_distance_m"] >= 0.0


def test_tier2_distance_extreme_aspect_ratio_needle(client, synthetic_car_pair):
    """B2.6: Extreme horizontal needle aspect ratio (width=1000, height=1) executes safely."""
    payload = dict(synthetic_car_pair)
    payload["object_a"] = {
        "id": "needle_h",
        "class_name": "car",
        "height": 1,
        "width": 1000,
        "center": [500.0, 300.0],
        "bbox": [0, 300, 1000, 301]
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True


def test_tier2_distance_extreme_aspect_ratio_tall(client, synthetic_car_pair):
    """B2.7: Extreme vertical needle aspect ratio (width=1, height=800) executes safely."""
    payload = dict(synthetic_car_pair)
    payload["object_a"] = {
        "id": "needle_v",
        "class_name": "person",
        "height": 800,
        "width": 1,
        "center": [500.0, 400.0],
        "bbox": [500, 0, 501, 800]
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True


def test_tier2_distance_zero_focal_length(client, synthetic_car_pair):
    """B2.8: focal_length_px=0 is rejected with 400 Bad Request or falls back safely without division by zero."""
    payload = dict(synthetic_car_pair)
    payload["focal_length_px"] = 0.0

    response = client.post("/api/distance", json=payload)
    assert response.status_code in [200, 400], (
        f"focal_length=0 should return 400 Bad Request or fall back safely, got {response.status_code}"
    )
    if response.status_code == 200:
        data = response.get_json()
        assert data["metrics"]["focal_length_px"] > 0


def test_tier2_distance_negative_focal_length(client, synthetic_car_pair):
    """B2.9: Negative focal length is rejected with 400 Bad Request or falls back safely without ZeroDivisionError."""
    payload = dict(synthetic_car_pair)
    payload["focal_length_px"] = -600.0

    response = client.post("/api/distance", json=payload)
    assert response.status_code in [200, 400], (
        f"Negative focal length should return 400 Bad Request or fall back safely, got {response.status_code}"
    )
    if response.status_code == 200:
        data = response.get_json()
        assert data["metrics"]["focal_length_px"] > 0


def test_tier2_distance_unknown_class_name(client, synthetic_car_pair):
    """B2.10: Unrecognized class name falls back gracefully to DEFAULT_REFERENCE_HEIGHT (1.50m)."""
    payload = dict(synthetic_car_pair)
    payload["object_a"] = dict(synthetic_car_pair["object_a"])
    payload["object_a"]["class_name"] = "unidentified_extraterrestrial_craft"

    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True
    # Depth calculated with 1.50m default height
    f = payload["focal_length_px"]
    h1 = payload["object_a"]["height"]
    expected_depth = (f * 1.50) / h1
    assert abs(data["object_a"]["estimated_depth_z"] - expected_depth) < 0.1


# ==============================================================================
# Feature 3: Protocol & Payload Boundaries (5 Test Cases)
# ==============================================================================

def test_tier2_oversized_payload_content_length(client):
    """B3.1: Request with oversized Content-Length (>16MB) is rejected with 413 or 400."""
    headers = {
        "Content-Length": str(17 * 1024 * 1024),
        "Content-Type": "multipart/form-data; boundary=boundary"
    }
    response = client.post("/api/detect", headers=headers, data=b"x" * 1024)
    assert response.status_code in [400, 413], (
        f"Oversized payload should be rejected with 413 or 400, got {response.status_code}"
    )


def test_tier2_malformed_json_body(client):
    """B3.2: Malformed JSON syntax in request body returns HTTP 400 Bad Request, not 500."""
    response = client.post(
        "/api/distance",
        data="{'this_is_bad_json': true,",
        content_type="application/json"
    )
    assert response.status_code == 400, (
        f"Malformed JSON must return 400 Bad Request, got {response.status_code}"
    )


def test_tier2_detect_conf_boundary_zero_and_one(client, sample_jpeg_bytes):
    """B3.3: Boundary confidence thresholds conf=0.0 and conf=1.0 are accepted."""
    for conf_val in ["0.0", "1.0"]:
        data = {
            "image": (io.BytesIO(sample_jpeg_bytes), "test.jpg"),
            "conf": conf_val
        }
        response = client.post("/api/detect", data=data, content_type="multipart/form-data")
        assert response.status_code == 200, (
            f"conf={conf_val} should be accepted, got {response.status_code}"
        )


def test_tier2_distance_null_image_dimensions(client, synthetic_car_pair):
    """B3.4: image_dimensions=None or empty dict falls back to default 1000x800 dimensions."""
    payload = dict(synthetic_car_pair)
    payload["image_dimensions"] = None

    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200, f"None image_dimensions should fall back safely, got {response.status_code}"
    data = response.get_json()
    assert data.get("success") is True


def test_tier2_corrupt_visualization_base64_in_distance(client, synthetic_car_pair):
    """B3.5: Corrupt image_base64 passed to /api/distance fails gracefully without crashing 500."""
    payload = dict(synthetic_car_pair)
    payload["image_base64"] = "corrupt_base64_not_an_image"

    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200, f"Distance metrics should still succeed with null visual, got {response.status_code}"
    data = response.get_json()
    assert data.get("success") is True
    assert data.get("visualization_image") is None
