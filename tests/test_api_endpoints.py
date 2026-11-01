"""Integration tests for all REST API endpoints (backend/routes/api.py and backend/app.py).

Tests:
- GET /: root info and advertised endpoints.
- GET /api/health: health check and service metadata.
- POST /api/detect: across all 6 ingestion formats (JPEG, PNG, WEBP, raw Base64, Data URL Base64, multipart).
- POST /api/distance: monocular projective depth and 3D Euclidean distance endpoint.
- 404 Not Found and 405 Method Not Allowed handling.
"""

import io
import json
import pytest


class TestAPIEndpoints:
    """Integration test suite for API endpoints."""

    # ---------------------------------------------------------
    # GET / and GET /api/health
    # ---------------------------------------------------------
    def test_root_index_endpoint(self, client):
        """GET / returns project info, status Online, and advertised endpoints."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert "project" in data
        assert "YOLO" in data["project"]
        assert data.get("status") == "Online"
        assert "api_endpoints" in data
        assert any("/api/detect" in ep for ep in data["api_endpoints"])
        assert any("/api/distance" in ep for ep in data["api_endpoints"])

    def test_root_index_disallows_mutating_verbs(self, client):
        """Root endpoint rejects mutating HTTP methods with 405."""
        assert client.post("/").status_code == 405
        assert client.put("/").status_code == 405
        assert client.delete("/").status_code == 405

    def test_health_check_endpoint(self, client):
        """GET /api/health returns 200 with service health and YOLO status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert data.get("status") == "healthy"
        assert "service" in data
        assert "yolo_loaded" in data
        assert "model_name" in data
        assert "domain" in data

    def test_health_disallows_mutating_verbs(self, client):
        """Health endpoint rejects mutating HTTP methods with 405."""
        assert client.post("/api/health").status_code == 405
        assert client.put("/api/health").status_code == 405
        assert client.delete("/api/health").status_code == 405

    def test_not_found_unknown_endpoint(self, client):
        """Unknown route returns HTTP 404 with standard JSON error."""
        response = client.get("/api/unknown_endpoint_xyz_123")
        assert response.status_code == 404
        assert response.is_json
        data = response.get_json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    # ---------------------------------------------------------
    # POST /api/detect - All Ingestion Formats
    # ---------------------------------------------------------
    def test_detect_multipart_jpeg(self, client, sample_jpeg_bytes):
        """Multipart upload with JPEG image returns 200 OK and valid detection schema."""
        response = client.post(
            "/api/detect",
            data={"image": (io.BytesIO(sample_jpeg_bytes), "sample.jpg")},
            content_type="multipart/form-data"
        )
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert data["success"] is True
        assert data["filename"] == "sample.jpg"
        assert "detections" in data
        assert "original_image" in data
        assert "annotated_image" in data

    def test_detect_multipart_png(self, client, sample_png_bytes):
        """Multipart upload with PNG image returns 200 OK."""
        response = client.post(
            "/api/detect",
            data={"image": (io.BytesIO(sample_png_bytes), "test_scene.png")},
            content_type="multipart/form-data"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["filename"] == "test_scene.png"

    def test_detect_multipart_webp(self, client, sample_webp_bytes):
        """Multipart upload with WEBP image returns 200 OK."""
        response = client.post(
            "/api/detect",
            data={"image": (io.BytesIO(sample_webp_bytes), "camera.webp")},
            content_type="multipart/form-data"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["filename"] == "camera.webp"

    def test_detect_json_raw_base64(self, client, sample_raw_base64):
        """POST JSON with raw Base64 image string returns 200 OK."""
        payload = {
            "image_base64": sample_raw_base64,
            "filename": "raw_capture.jpg"
        }
        response = client.post("/api/detect", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["filename"] == "raw_capture.jpg"
        assert isinstance(data["detections"], list)

    def test_detect_json_data_url_base64(self, client, sample_base64_data_url):
        """POST JSON with standard data:image/jpeg;base64,... Data URL returns 200 OK."""
        payload = {
            "image_base64": sample_base64_data_url,
            "filename": "webcam.jpg"
        }
        response = client.post("/api/detect", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "detections" in data

    def test_detect_json_png_data_url(self, client, sample_png_data_url):
        """POST JSON with data:image/png;base64,... Data URL returns 200 OK."""
        payload = {
            "image_base64": sample_png_data_url,
            "filename": "screenshot.png"
        }
        response = client.post("/api/detect", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_detect_custom_thresholds_json(self, client, sample_base64_data_url):
        """POST JSON accepting custom conf and iou filter thresholds."""
        payload = {
            "image_base64": sample_base64_data_url,
            "conf": 0.45,
            "iou": 0.35
        }
        response = client.post("/api/detect", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_detect_custom_thresholds_multipart(self, client, sample_jpeg_bytes):
        """Multipart form upload accepting custom conf and iou fields."""
        response = client.post(
            "/api/detect",
            data={
                "image": (io.BytesIO(sample_jpeg_bytes), "sample.jpg"),
                "conf": "0.50",
                "iou": "0.40"
            },
            content_type="multipart/form-data"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_detect_full_response_schema_contract(self, client, sample_base64_data_url):
        """Response satisfies complete schema contract from PROJECT.md."""
        response = client.post("/api/detect", json={"image_base64": sample_base64_data_url})
        assert response.status_code == 200
        data = response.get_json()

        # Check all top-level keys
        assert "success" in data
        assert "model_used" in data
        assert "inference_time_ms" in data
        assert "image_dimensions" in data
        assert "width" in data["image_dimensions"]
        assert "height" in data["image_dimensions"]
        assert "total_objects" in data
        assert "detections" in data
        assert "original_image" in data
        assert "annotated_image" in data
        assert "classes_detected" in data
        assert "filename" in data

    # ---------------------------------------------------------
    # POST /api/distance - Calculations & Schema
    # ---------------------------------------------------------
    def test_distance_standard_payload(self, client, synthetic_car_pair):
        """POST /api/distance calculates monocular depth and 3D Euclidean separation."""
        response = client.post("/api/distance", json=synthetic_car_pair)
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()

        assert data["success"] is True
        assert "depth_object_a" in data
        assert "depth_object_b" in data
        assert "distance_3d_meters" in data
        assert "pixel_distance" in data
        assert "normalized_distance_pct" in data
        assert "focal_length_px" in data
        assert data["focal_length_px"] == synthetic_car_pair["focal_length_px"]

        assert "object_a" in data
        assert "object_b" in data
        assert "metrics" in data

    def test_distance_metrics_subschema(self, client, synthetic_car_pair):
        """Metrics object contains breakdown of 2D/3D metrics and disclaimer."""
        response = client.post("/api/distance", json=synthetic_car_pair)
        assert response.status_code == 200
        data = response.get_json()
        metrics = data["metrics"]

        assert "pixel_distance_px" in metrics
        assert "delta_x_pixels" in metrics
        assert "delta_y_pixels" in metrics
        assert "normalized_distance_pct" in metrics
        assert "estimated_relative_distance_m" in metrics
        assert "disclaimer" in metrics

    def test_distance_custom_reference_heights(self, client, synthetic_car_pair):
        """Passing custom reference heights overrides default physical class priors."""
        payload = dict(synthetic_car_pair)
        payload["custom_ref_height_a"] = 2.0
        payload["custom_ref_height_b"] = 1.8

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["depth_object_a"] > 0
        assert data["depth_object_b"] > 0

    def test_distance_with_visualization_image(self, client, synthetic_car_pair, sample_base64_data_url):
        """Supplying base image generates annotated visualization with measurement overlay."""
        payload = dict(synthetic_car_pair)
        payload["image_base64"] = sample_base64_data_url

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["visualization_image"] is not None
        assert data["visualization_image"].startswith("data:image/jpeg;base64,")

    def test_distance_omitted_focal_length_adaptive_default(self, client, synthetic_car_pair):
        """Omitted focal length automatically adapts to 0.9 * image width."""
        payload = dict(synthetic_car_pair)
        del payload["focal_length_px"]

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # Width is 960 -> 960 * 0.9 = 864.0
        assert data["focal_length_px"] == 864.0

    def test_distance_forklift_and_person_warehouse_scenario(self, client, synthetic_forklift_pair):
        """Industrial warehouse scenario: forklift prior (2.20m) and person (1.70m)."""
        response = client.post("/api/distance", json=synthetic_forklift_pair)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["distance_3d_meters"] > 0.0
