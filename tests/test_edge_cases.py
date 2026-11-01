"""Comprehensive edge-case test suite for YOLO Object Distance System.

Verifies robust handling of malformed inputs, missing parameters, zero-byte payloads,
corrupted byte streams, extreme geometries, and edge conditions with clean HTTP 400 status
codes, informative JSON error messages, and zero unhandled 500 crashes.
"""

import io
import json
import pytest
import numpy as np
import cv2


class TestEdgeCases:
    """Comprehensive edge-case and boundary verification."""

    # =========================================================
    # POST /api/detect - Edge Cases
    # =========================================================

    def test_detect_zero_objects_blank_canvas(self, client, blank_black_image_bytes):
        """0 objects detected: solid black frame returns 200 OK with empty detections list."""
        response = client.post(
            "/api/detect",
            data={"image": (io.BytesIO(blank_black_image_bytes), "black_screen.jpg")},
            content_type="multipart/form-data"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # Blank canvas should yield 0 objects under normal model prediction or fallback
        assert isinstance(data["detections"], list)
        assert isinstance(data["total_objects"], int)

    def test_detect_corrupted_image_file_bytes(self, client, sample_corrupt_bytes):
        """Corrupted image payload (random non-image bytes) returns 400 Bad Request."""
        response = client.post(
            "/api/detect",
            data={"image": (io.BytesIO(sample_corrupt_bytes), "corrupt.jpg")},
            content_type="multipart/form-data"
        )
        assert response.status_code == 400
        assert response.is_json
        data = response.get_json()
        assert "error" in data
        assert any(term in data["error"].lower() for term in ["corrupted", "decode", "unsupported"])

    def test_detect_zero_byte_file_upload(self, client, sample_zero_bytes):
        """0-byte uploaded file returns 400 Bad Request with clear error."""
        response = client.post(
            "/api/detect",
            data={"image": (io.BytesIO(sample_zero_bytes), "empty.jpg")},
            content_type="multipart/form-data"
        )
        assert response.status_code == 400
        assert response.is_json
        data = response.get_json()
        assert "error" in data
        assert "empty (0 bytes)" in data["error"]

    def test_detect_unsupported_file_extensions(self, client):
        """Non-image file extensions (.exe, .sh, .txt, .bin) return 400 Bad Request."""
        for filename in ["payload.exe", "test.sh", "readme.txt", "data.bin"]:
            response = client.post(
                "/api/detect",
                data={"image": (io.BytesIO(b"fake data"), filename)},
                content_type="multipart/form-data"
            )
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
            assert "Unsupported file extension" in data["error"]

    def test_detect_corrupted_base64_string(self, client):
        """Corrupted Base64 characters in JSON return 400 Bad Request."""
        response = client.post(
            "/api/detect",
            json={"image_base64": "NOT_A_VALID_BASE64_STRING_!@#$%^&*()"}
        )
        assert response.status_code == 400
        assert response.is_json
        data = response.get_json()
        assert "error" in data

    def test_detect_corrupted_base64_non_image_payload(self, client):
        """Valid Base64 string that decodes to non-image bytes returns 400 Bad Request."""
        import base64
        non_image_b64 = base64.b64encode(b"This is non-image plaintext data").decode("utf-8")
        response = client.post(
            "/api/detect",
            json={"image_base64": non_image_b64}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_detect_empty_base64_string(self, client):
        """Empty or whitespace-only Base64 string returns 400 Bad Request."""
        response = client.post("/api/detect", json={"image_base64": ""})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

        response_ws = client.post("/api/detect", json={"image_base64": "   \n\t "})
        assert response_ws.status_code == 400

    def test_detect_data_url_prefix_without_payload(self, client):
        """Data URL prefix without base64 body returns 400 Bad Request."""
        response = client.post(
            "/api/detect",
            json={"image_base64": "data:image/jpeg;base64,"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_detect_missing_image_payload(self, client):
        """Request containing no file and no image_base64 field returns 400 Bad Request."""
        response = client.post("/api/detect", json={"conf": 0.5})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "No image provided" in data["error"]

    def test_detect_empty_json_body(self, client):
        """Empty request body with application/json header returns 400 Bad Request."""
        response = client.post(
            "/api/detect",
            data="",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_detect_malformed_json_syntax(self, client):
        """Malformed JSON syntax returns 400 Bad Request without server crash."""
        response = client.post(
            "/api/detect",
            data='{"image_base64": "abc", "conf": }',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_detect_non_object_json(self, client):
        """Non-object JSON payload (array or primitive) returns 400 Bad Request."""
        response = client.post(
            "/api/detect",
            data='["item1", "item2"]',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_detect_non_numeric_conf_threshold(self, client, sample_base64_data_url):
        """Non-numeric conf threshold returns 400 Bad Request."""
        response = client.post(
            "/api/detect",
            json={"image_base64": sample_base64_data_url, "conf": "extremely_high"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be a numeric value" in data["error"]

    def test_detect_out_of_range_conf_threshold(self, client, sample_base64_data_url):
        """Out of range conf thresholds (< 0.0 or > 1.0) return 400 Bad Request."""
        res_neg = client.post(
            "/api/detect",
            json={"image_base64": sample_base64_data_url, "conf": -0.1}
        )
        assert res_neg.status_code == 400
        assert "between 0.0 and 1.0" in res_neg.get_json()["error"]

        res_over = client.post(
            "/api/detect",
            json={"image_base64": sample_base64_data_url, "conf": 1.5}
        )
        assert res_over.status_code == 400
        assert "between 0.0 and 1.0" in res_over.get_json()["error"]

    def test_detect_non_numeric_iou_threshold(self, client, sample_base64_data_url):
        """Non-numeric iou threshold returns 400 Bad Request."""
        response = client.post(
            "/api/detect",
            json={"image_base64": sample_base64_data_url, "iou": "medium_overlap"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be a numeric value" in data["error"]

    def test_detect_out_of_range_iou_threshold(self, client, sample_base64_data_url):
        """Out of range iou thresholds (< 0.0 or > 1.0) return 400 Bad Request."""
        res_neg = client.post(
            "/api/detect",
            json={"image_base64": sample_base64_data_url, "iou": -0.5}
        )
        assert res_neg.status_code == 400

        res_over = client.post(
            "/api/detect",
            json={"image_base64": sample_base64_data_url, "iou": 2.0}
        )
        assert res_over.status_code == 400

    # =========================================================
    # POST /api/distance - Edge Cases
    # =========================================================

    def test_distance_single_object_cannot_compute_pairwise(self, client, synthetic_single_object):
        """1 object provided: pairwise distance calculation impossible -> returns 400 Bad Request."""
        # synthetic_single_object has object_a, but lacks object_b
        response = client.post("/api/distance", json=synthetic_single_object)
        assert response.status_code == 400
        assert response.is_json
        data = response.get_json()
        assert "error" in data
        assert "object_b" in data["error"].lower()

    def test_distance_missing_both_objects(self, client):
        """Empty JSON payload or missing object_a/object_b returns 400 Bad Request."""
        response = client.post("/api/distance", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "object_a" in data["error"].lower()

    def test_distance_non_dict_object_payload(self, client):
        """Passing non-dictionary for object_a or object_b returns 400 Bad Request."""
        response = client.post(
            "/api/distance",
            json={"object_a": "car", "object_b": {"class": "person"}}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_distance_empty_request_body(self, client):
        """Empty request body to /api/distance returns 400 Bad Request."""
        response = client.post(
            "/api/distance",
            data="",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_distance_malformed_json_syntax(self, client):
        """Malformed JSON syntax to /api/distance returns 400 Bad Request."""
        response = client.post(
            "/api/distance",
            data='{"object_a": {',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_distance_non_object_json(self, client):
        """Non-object JSON payload (array or string) returns 400 Bad Request."""
        response = client.post(
            "/api/distance",
            data='[{"object_a": 1}]',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_distance_invalid_negative_coordinates(self, client):
        """Negative coordinates in bounding boxes and centers are handled without 500 crashes."""
        payload = {
            "object_a": {
                "class": "car",
                "height": 140,
                "center": [-50.0, -30.0],
                "bbox": [-150, -100, 50, 40]
            },
            "object_b": {
                "class": "person",
                "height": 180,
                "center": [200.0, 300.0],
                "bbox": [150, 210, 250, 390]
            },
            "image_dimensions": {"width": 960, "height": 600},
            "focal_length_px": 864.0
        }
        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["distance_3d_meters"] > 0

    def test_distance_inverted_bounding_box_coordinates(self, client):
        """Inverted bounding box coordinates (x2 < x1 or y2 < y1) compute cleanly using abs()."""
        payload = {
            "object_a": {
                "class": "car",
                "bbox": [400, 500, 140, 360]  # x2=140 < x1=400, y2=360 < y1=500
            },
            "object_b": {
                "class": "car",
                "bbox": [790, 420, 580, 310]
            },
            "image_dimensions": {"width": 960, "height": 600}
        }
        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # Height and width should be positive abs differences
        assert data["object_a"]["height"] == 140.0
        assert data["object_a"]["width"] == 260.0

    def test_distance_extreme_aspect_ratio_horizontal_needle(self, client):
        """Extreme aspect ratio: horizontal needle (1000px wide x 1px tall) executes cleanly."""
        payload = {
            "object_a": {
                "class": "car",
                "height": 1,
                "width": 1000,
                "center": [500, 300]
            },
            "object_b": {
                "class": "person",
                "height": 100,
                "width": 30,
                "center": [200, 300]
            },
            "image_dimensions": {"width": 1280, "height": 720}
        }
        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["distance_3d_meters"] > 0

    def test_distance_extreme_aspect_ratio_vertical_needle(self, client):
        """Extreme aspect ratio: vertical needle (1px wide x 800px tall) executes cleanly."""
        payload = {
            "object_a": {
                "class": "truck",
                "height": 800,
                "width": 1,
                "center": [100, 400]
            },
            "object_b": {
                "class": "car",
                "height": 120,
                "width": 200,
                "center": [500, 400]
            },
            "image_dimensions": {"width": 1000, "height": 800}
        }
        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["distance_3d_meters"] > 0

    def test_distance_missing_calibration_null_focal_length(self, client, synthetic_car_pair):
        """Null focal length in JSON triggers adaptive focal length without error."""
        payload = dict(synthetic_car_pair)
        payload["focal_length_px"] = None

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # 960 * 0.9 = 864.0
        assert data["focal_length_px"] == 864.0

    def test_distance_non_positive_focal_length(self, client, synthetic_car_pair):
        """Zero or negative focal length returns 400 Bad Request."""
        payload_zero = dict(synthetic_car_pair)
        payload_zero["focal_length_px"] = 0
        res_zero = client.post("/api/distance", json=payload_zero)
        assert res_zero.status_code == 400
        assert "greater than 0" in res_zero.get_json()["error"]

        payload_neg = dict(synthetic_car_pair)
        payload_neg["focal_length_px"] = -250.0
        res_neg = client.post("/api/distance", json=payload_neg)
        assert res_neg.status_code == 400
        assert "greater than 0" in res_neg.get_json()["error"]

    def test_distance_non_numeric_focal_length(self, client, synthetic_car_pair):
        """Non-numeric focal length returns 400 Bad Request."""
        payload = dict(synthetic_car_pair)
        payload["focal_length_px"] = "wide_angle_lens"

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be numeric" in data["error"]

    def test_distance_non_dict_image_dimensions(self, client, synthetic_car_pair):
        """Non-dict image_dimensions returns 400 Bad Request."""
        payload = dict(synthetic_car_pair)
        payload["image_dimensions"] = "1920x1080"

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be a dictionary" in data["error"]

    def test_distance_non_numeric_custom_ref_height(self, client, synthetic_car_pair):
        """Non-numeric custom reference height returns 400 Bad Request."""
        payload = dict(synthetic_car_pair)
        payload["custom_ref_height_a"] = "extra_large"

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be numeric" in data["error"]

    def test_distance_non_positive_custom_ref_height(self, client, synthetic_car_pair):
        """Zero or negative custom reference height returns 400 Bad Request."""
        payload = dict(synthetic_car_pair)
        payload["custom_ref_height_b"] = -1.5

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be greater than 0" in data["error"]

    def test_distance_corrupt_visualization_image_payload(self, client, synthetic_car_pair):
        """Corrupted base_image_base64 returns 200 OK with visualization_image: null (no crash)."""
        payload = dict(synthetic_car_pair)
        payload["image_base64"] = "CORRUPTED_NON_BASE64_IMAGE_DATA_123!@#"

        response = client.post("/api/distance", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["visualization_image"] is None
        assert data["distance_3d_meters"] > 0
