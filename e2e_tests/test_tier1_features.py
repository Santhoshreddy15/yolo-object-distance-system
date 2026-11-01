"""Tier 1: Feature Coverage E2E Tests.

Validates primary functionality (happy path and fundamental contracts) across:
- Feature 1: GET / (Root Metadata)
- Feature 2: GET /api/health (Service Health & Model Status)
- Feature 3: POST /api/detect (Object Detection via Multipart & Base64)
- Feature 4: POST /api/distance (3D Monocular Euclidean Distance Estimation)
- Feature 5: Global Routing & Protocol Handlers (404 and CORS)

Each feature contains at least 5 distinct test cases.
"""

import io
import math
import pytest


# ==============================================================================
# Feature 1: GET / (Root Service Metadata) - 5 Test Cases
# ==============================================================================

def test_tier1_root_endpoint_status_200(client):
    """F1.1: Root endpoint must return HTTP 200 OK."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_tier1_root_content_type_json(client):
    """F1.2: Root endpoint must return application/json content type."""
    response = client.get("/")
    assert "application/json" in response.headers.get("Content-Type", ""), (
        f"Expected application/json in Content-Type, got {response.headers.get('Content-Type')}"
    )


def test_tier1_root_project_metadata(client):
    """F1.3: Root endpoint returns required project metadata fields."""
    response = client.get("/")
    data = response.get_json()
    assert isinstance(data, dict), "Response must be a JSON object"
    assert "project" in data and len(data["project"]) > 0, "Missing 'project' name"
    assert "domain" in data and len(data["domain"]) > 0, "Missing 'domain' description"
    assert data.get("status") == "Online", f"Expected status 'Online', got {data.get('status')}"


def test_tier1_root_api_endpoints_declared(client):
    """F1.4: Root endpoint advertises available API routes."""
    response = client.get("/")
    data = response.get_json()
    endpoints = data.get("api_endpoints", [])
    assert isinstance(endpoints, list), "'api_endpoints' must be a list"
    assert len(endpoints) >= 3, "Expected at least 3 advertised endpoints"
    endpoint_strs = " ".join(endpoints)
    assert "/api/health" in endpoint_strs
    assert "/api/detect" in endpoint_strs
    assert "/api/distance" in endpoint_strs


def test_tier1_root_unsupported_http_methods(client):
    """F1.5: Root endpoint rejects POST/PUT/DELETE with 405 Method Not Allowed."""
    for method in ["post", "put", "delete"]:
        caller = getattr(client, method)
        response = caller("/")
        assert response.status_code == 405, (
            f"Expected 405 for {method.upper()} /, got {response.status_code}"
        )


# ==============================================================================
# Feature 2: GET /api/health (Service Health & Model Status) - 5 Test Cases
# ==============================================================================

def test_tier1_health_status_200(client):
    """F2.1: Health endpoint returns HTTP 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_tier1_health_content_type_json(client):
    """F2.2: Health endpoint returns application/json."""
    response = client.get("/api/health")
    assert "application/json" in response.headers.get("Content-Type", "")


def test_tier1_health_response_schema(client):
    """F2.3: Health endpoint payload adheres to contract schema."""
    response = client.get("/api/health")
    data = response.get_json()
    assert isinstance(data, dict), "Health response must be a JSON object"
    expected_fields = ["status", "service", "yolo_loaded", "model_name", "load_error", "domain"]
    for field in expected_fields:
        assert field in data, f"Missing required field '{field}' in health response"


def test_tier1_health_service_identity(client):
    """F2.4: Health endpoint reports status 'healthy' and YOLO service name."""
    response = client.get("/api/health")
    data = response.get_json()
    assert data.get("status") == "healthy", f"Expected healthy status, got {data.get('status')}"
    assert "YOLO" in data.get("service", ""), f"Service name should mention YOLO, got {data.get('service')}"
    assert isinstance(data.get("yolo_loaded"), bool), "'yolo_loaded' must be boolean"


def test_tier1_health_unsupported_http_methods(client):
    """F2.5: Health endpoint rejects mutating HTTP methods with 405."""
    for method in ["post", "put", "delete"]:
        caller = getattr(client, method)
        response = caller("/api/health")
        assert response.status_code == 405, (
            f"Expected 405 for {method.upper()} /api/health, got {response.status_code}"
        )


# ==============================================================================
# Feature 3: POST /api/detect (Object Detection) - 7 Test Cases
# ==============================================================================

def test_tier1_detect_multipart_jpeg_success(client, sample_jpeg_bytes):
    """F3.1: Detection succeeds with standard JPEG multipart upload."""
    data = {
        "image": (io.BytesIO(sample_jpeg_bytes), "sample_scene.jpg")
    }
    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
    body = response.get_json()
    assert body.get("success") is True
    assert "detections" in body
    assert body.get("filename") == "sample_scene.jpg"


def test_tier1_detect_multipart_png_success(client, sample_png_bytes):
    """F3.2: Detection succeeds with PNG multipart upload."""
    data = {
        "image": (io.BytesIO(sample_png_bytes), "scene.png")
    }
    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    body = response.get_json()
    assert body.get("success") is True
    assert body.get("image_dimensions", {}).get("width") == 640
    assert body.get("image_dimensions", {}).get("height") == 480


def test_tier1_detect_multipart_webp_success(client, sample_webp_bytes):
    """F3.3: Detection succeeds with WEBP multipart upload."""
    data = {
        "image": (io.BytesIO(sample_webp_bytes), "scene.webp")
    }
    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    body = response.get_json()
    assert body.get("success") is True


def test_tier1_detect_json_base64_data_url_success(client, sample_base64_data_url):
    """F3.4: Detection succeeds with JSON payload containing data:image/jpeg;base64 URL."""
    payload = {
        "image_base64": sample_base64_data_url,
        "filename": "camera_frame_01.jpg"
    }
    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200
    body = response.get_json()
    assert body.get("success") is True
    assert "annotated_image" in body
    assert body["annotated_image"].startswith("data:image/jpeg;base64,")


def test_tier1_detect_json_raw_base64_success(client, sample_raw_base64):
    """F3.5: Detection succeeds with raw Base64 string without data URI prefix."""
    payload = {
        "image_base64": sample_raw_base64
    }
    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200
    body = response.get_json()
    assert body.get("success") is True


def test_tier1_detect_custom_conf_and_iou_thresholds(client, sample_jpeg_bytes):
    """F3.6: Detection accepts custom confidence and IoU thresholds."""
    data = {
        "image": (io.BytesIO(sample_jpeg_bytes), "scene.jpg"),
        "conf": "0.55",
        "iou": "0.35"
    }
    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    body = response.get_json()
    assert body.get("success") is True


def test_tier1_detect_response_schema_and_bounding_boxes(client, sample_jpeg_bytes):
    """F3.7: Detection response strictly contains all specified schema attributes."""
    data = {"image": (io.BytesIO(sample_jpeg_bytes), "test.jpg")}
    response = client.post("/api/detect", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    body = response.get_json()

    for field in ["success", "model_used", "inference_time_ms", "image_dimensions", "total_objects", "detections", "original_image", "annotated_image"]:
        assert field in body, f"Missing top-level field '{field}'"

    assert isinstance(body["detections"], list)
    for det in body["detections"]:
        assert "id" in det
        assert "class_name" in det
        assert "confidence" in det and 0.0 <= det["confidence"] <= 1.0
        assert "bbox" in det and len(det["bbox"]) == 4
        assert "center" in det and len(det["center"]) == 2
        assert "width" in det and det["width"] >= 0
        assert "height" in det and det["height"] >= 0


# ==============================================================================
# Feature 4: POST /api/distance (3D Distance Estimation) - 7 Test Cases
# ==============================================================================

def test_tier1_distance_standard_two_objects_200(client, synthetic_car_pair):
    """F4.1: Distance endpoint succeeds with two standard detected objects."""
    response = client.post("/api/distance", json=synthetic_car_pair)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
    data = response.get_json()
    assert data.get("success") is True


def test_tier1_distance_response_schema(client, synthetic_car_pair):
    """F4.2: Distance response schema contains objects, metrics, and disclaimer."""
    response = client.post("/api/distance", json=synthetic_car_pair)
    assert response.status_code == 200
    data = response.get_json()

    assert "object_a" in data and "object_b" in data
    assert "metrics" in data
    metrics = data["metrics"]

    assert "pixel_distance" in metrics
    assert "normalized_distance_pct" in metrics
    assert "estimated_relative_distance_m" in metrics
    assert "focal_length_px" in metrics
    assert metrics["estimated_relative_distance_m"] > 0.0


def test_tier1_distance_pinhole_depth_calculation(client, synthetic_car_pair):
    """F4.3: Estimated depths Z_1, Z_2 match projective pinhole formula Z = (f * H) / h."""
    response = client.post("/api/distance", json=synthetic_car_pair)
    assert response.status_code == 200
    data = response.get_json()

    f = synthetic_car_pair["focal_length_px"] # 864.0
    h1 = synthetic_car_pair["object_a"]["height"] # 140
    h2 = synthetic_car_pair["object_b"]["height"] # 110
    car_ref_h = 1.50 # Standard car reference height

    expected_z1 = (f * car_ref_h) / h1 # 864.0 * 1.5 / 140 = 9.2571
    expected_z2 = (f * car_ref_h) / h2 # 864.0 * 1.5 / 110 = 11.7818

    actual_z1 = data["object_a"]["estimated_depth_z"]
    actual_z2 = data["object_b"]["estimated_depth_z"]

    assert abs(actual_z1 - expected_z1) < 0.1, f"Z1 {actual_z1} != expected {expected_z1}"
    assert abs(actual_z2 - expected_z2) < 0.1, f"Z2 {actual_z2} != expected {expected_z2}"


def test_tier1_distance_with_visualization_base64(client, synthetic_car_pair, sample_base64_data_url):
    """F4.4: Submitting base image base64 generates visualization image with annotations."""
    payload = dict(synthetic_car_pair)
    payload["image_base64"] = sample_base64_data_url

    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data.get("visualization_image") is not None
    assert data["visualization_image"].startswith("data:image/jpeg;base64,")


def test_tier1_distance_default_focal_length_fallback(client, synthetic_car_pair):
    """F4.5: Omitting focal_length_px falls back to 0.9 * image_width."""
    payload = dict(synthetic_car_pair)
    del payload["focal_length_px"]
    payload["image_dimensions"] = {"width": 1000, "height": 600}

    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    expected_focal = 1000 * 0.9 # 900.0
    actual_focal = data["metrics"]["focal_length_px"]
    assert abs(actual_focal - expected_focal) < 1.0, f"Expected {expected_focal}, got {actual_focal}"


def test_tier1_distance_identical_objects_zero_separation(client):
    """F4.6: Calculating distance between an object and itself yields 0.0m Euclidean distance."""
    same_obj = {
        "id": "single_car",
        "class_name": "car",
        "height": 140,
        "center": [300.0, 400.0],
        "bbox": [200, 330, 400, 470]
    }
    payload = {
        "object_a": same_obj,
        "object_b": same_obj,
        "image_dimensions": {"width": 800, "height": 600},
        "focal_length_px": 800.0
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    dist_m = data["metrics"]["estimated_relative_distance_m"]
    assert dist_m == 0.0, f"Expected 0.0m distance for identical co-located objects, got {dist_m}"


def test_tier1_distance_unsupported_http_methods(client):
    """F4.7: Distance endpoint rejects GET/PUT/DELETE with 405 Method Not Allowed."""
    for method in ["get", "put", "delete"]:
        caller = getattr(client, method)
        response = caller("/api/distance")
        assert response.status_code == 405, (
            f"Expected 405 for {method.upper()} /api/distance, got {response.status_code}"
        )


# ==============================================================================
# Feature 5: Global Routing & Protocol Handlers - 5 Test Cases
# ==============================================================================

def test_tier1_global_404_not_found_status(client):
    """F5.1: Non-existent route returns HTTP 404 Not Found."""
    response = client.get("/api/non_existent_endpoint_xyz")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


def test_tier1_global_404_json_payload(client):
    """F5.2: 404 handler returns clean JSON error response."""
    response = client.get("/api/does_not_exist")
    assert response.status_code == 404
    data = response.get_json()
    assert isinstance(data, dict)
    assert "error" in data
    assert data["error"] == "Endpoint not found"


def test_tier1_cors_headers_on_api(client):
    """F5.3: Cross-Origin Resource Sharing headers present on API routes."""
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") in ["*", "http://localhost:3000"]


def test_tier1_head_request_on_root(client):
    """F5.4: HEAD request to root returns 200 with empty body."""
    response = client.head("/")
    assert response.status_code == 200
    assert len(response.data) == 0


def test_tier1_options_preflight_on_api(client):
    """F5.5: OPTIONS preflight request to /api/detect is accepted."""
    response = client.options("/api/detect", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST"
    })
    assert response.status_code in [200, 204]
