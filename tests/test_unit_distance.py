"""Unit tests for DistanceEstimatorService (backend/services/distance_estimator.py).

Tests projective depth calculation, 3D Euclidean distance projection, class priors,
custom height overrides, center extraction formats, defensive zero-division clamping,
adaptive focal length fallbacks, and visual measurement generation.
"""

import math
import pytest
import numpy as np
import cv2

from backend.services.distance_estimator import (
    DistanceEstimatorService,
    CLASS_REFERENCE_HEIGHTS,
    DEFAULT_REFERENCE_HEIGHT
)


class TestDistanceEstimatorService:
    """Unit tests for DistanceEstimatorService."""

    def test_distance_service_initialization(self):
        """Service initializes cleanly without error."""
        service = DistanceEstimatorService()
        assert service is not None

    def test_class_reference_heights_priors(self):
        """Reference heights match expected architectural physical priors."""
        assert CLASS_REFERENCE_HEIGHTS["car"] == 1.50
        assert CLASS_REFERENCE_HEIGHTS["person"] == 1.70
        assert CLASS_REFERENCE_HEIGHTS["forklift"] == 2.20
        assert CLASS_REFERENCE_HEIGHTS["bus"] == 3.20
        assert CLASS_REFERENCE_HEIGHTS["truck"] == 3.00
        assert CLASS_REFERENCE_HEIGHTS["bicycle"] == 1.00
        assert CLASS_REFERENCE_HEIGHTS["motorcycle"] == 1.10
        assert DEFAULT_REFERENCE_HEIGHT == 1.50

    def test_projective_depth_calculation_analytical(self):
        """Monocular depth Z = (f * H_real) / h_pixels matches analytical ground truth."""
        service = DistanceEstimatorService()
        focal_px = 1000.0
        h_real = 1.50   # Car reference height (1.50m)
        h_px = 150.0    # 150 pixels on sensor
        # Z should be exactly (1000 * 1.50) / 150 = 10.0m

        obj_a = {"class": "car", "height": h_px, "center": [480, 300]}
        obj_b = {"class": "car", "height": h_px, "center": [480, 300]}

        result = service.calculate_distance(
            object_a=obj_a,
            object_b=obj_b,
            image_dimensions={"width": 960, "height": 600},
            focal_length_px=focal_px
        )

        assert result["success"] is True
        assert abs(result["depth_object_a"] - 10.0) < 0.05
        assert abs(result["depth_object_b"] - 10.0) < 0.05

    def test_camera_3d_coordinates_and_euclidean_distance(self):
        """Relative 3D Euclidean distance matches coordinate projection geometry."""
        service = DistanceEstimatorService()
        img_w, img_h = 1000.0, 800.0
        c_x, c_y = 500.0, 400.0
        focal_px = 1000.0

        # Object A placed exactly at principal center (cx1=500, cy1=400), h=200 -> Z1 = 1000*1.5/200 = 7.5m
        # Camera coords: X1 = 0, Y1 = 0, Z1 = 7.5
        obj_a = {"class": "car", "height": 200, "center": [500, 400]}

        # Object B placed horizontally at cx2=700, cy2=400, h=200 -> Z2 = 7.5m
        # Camera coords: X2 = (700 - 500)*7.5 / 1000 = 1.5m, Y2 = 0, Z2 = 7.5m
        # 3D distance between A and B should be exactly 1.5m!
        obj_b = {"class": "car", "height": 200, "center": [700, 400]}

        result = service.calculate_distance(
            object_a=obj_a,
            object_b=obj_b,
            image_dimensions={"width": img_w, "height": img_h},
            focal_length_px=focal_px
        )

        assert result["success"] is True
        assert abs(result["depth_object_a"] - 7.5) < 0.05
        assert abs(result["depth_object_b"] - 7.5) < 0.05
        assert abs(result["distance_3d_meters"] - 1.50) < 0.05

    def test_colocated_identical_objects_zero_distance(self):
        """Co-located identical objects yield 0.0m 3D distance."""
        service = DistanceEstimatorService()
        obj = {"class": "car", "height": 120, "center": [300, 250], "bbox": [200, 190, 400, 310]}

        result = service.calculate_distance(
            object_a=obj,
            object_b=obj,
            image_dimensions={"width": 960, "height": 600},
            focal_length_px=800.0
        )

        assert result["success"] is True
        assert result["pixel_distance"] == 0.0
        assert result["distance_3d_meters"] == 0.0

    def test_distance_calculation_symmetry(self):
        """Calculations are symmetric: Dist(A, B) == Dist(B, A)."""
        service = DistanceEstimatorService()
        obj_a = {"class": "truck", "height": 180, "center": [200, 350], "bbox": [100, 260, 300, 440]}
        obj_b = {"class": "person", "height": 90, "center": [650, 420], "bbox": [620, 375, 680, 465]}

        res_ab = service.calculate_distance(obj_a, obj_b, {"width": 960, "height": 600}, focal_length_px=850.0)
        res_ba = service.calculate_distance(obj_b, obj_a, {"width": 960, "height": 600}, focal_length_px=850.0)

        assert res_ab["success"] is True
        assert res_ba["success"] is True
        assert res_ab["distance_3d_meters"] == res_ba["distance_3d_meters"]
        assert res_ab["pixel_distance"] == res_ba["pixel_distance"]
        assert res_ab["normalized_distance_pct"] == res_ba["normalized_distance_pct"]

    def test_unknown_class_fallback_to_default_height(self):
        """Unknown class names fallback to DEFAULT_REFERENCE_HEIGHT (1.50m)."""
        service = DistanceEstimatorService()
        obj_unknown = {"class": "industrial_drone_x9", "height": 150, "center": [480, 300]}
        obj_car = {"class": "car", "height": 150, "center": [480, 300]}

        res = service.calculate_distance(
            object_a=obj_unknown,
            object_b=obj_car,
            image_dimensions={"width": 960, "height": 600},
            focal_length_px=1000.0
        )

        # Since car is 1.50m and default fallback is 1.50m, depths must match exactly
        assert res["depth_object_a"] == res["depth_object_b"]

    def test_custom_reference_height_override(self):
        """Custom reference height overrides default class prior."""
        service = DistanceEstimatorService()
        obj_a = {"class": "car", "height": 100, "center": [480, 300]}
        obj_b = {"class": "car", "height": 100, "center": [480, 300]}

        # Override object_a to 3.0m (double car's default 1.5m)
        res = service.calculate_distance(
            object_a=obj_a,
            object_b=obj_b,
            image_dimensions={"width": 960, "height": 600},
            focal_length_px=1000.0,
            custom_ref_height_a=3.0,
            custom_ref_height_b=1.5
        )

        assert res["depth_object_a"] == round(res["depth_object_b"] * 2.0, 2)

    def test_flexible_center_formats(self):
        """Center coordinates can be supplied via center list, centroid dict, or bbox."""
        service = DistanceEstimatorService()

        # Center as [x, y]
        o1 = {"class": "car", "height": 100, "center": [300, 200]}
        # Centroid as {"x": x, "y": y}
        o2 = {"class": "car", "height": 100, "centroid": {"x": 300, "y": 200}}
        # Bbox only [x1, y1, x2, y2] -> center is [(100+500)/2, (100+300)/2] = [300, 200]
        o3 = {"class": "car", "bbox": [100, 100, 500, 300]}

        res_12 = service.calculate_distance(o1, o2)
        res_13 = service.calculate_distance(o1, o3)

        assert res_12["pixel_distance"] == 0.0
        assert res_13["pixel_distance"] == 0.0

    def test_dimension_extraction_fallbacks(self):
        """Height/width fallback to bbox difference or 100.0 when missing or None."""
        service = DistanceEstimatorService()

        # Object with explicit None height but valid bbox [0, 50, 100, 250] (height=200)
        obj_a = {"class": "car", "height": None, "bbox": [0, 50, 100, 250], "center": [50, 150]}
        obj_b = {"class": "car", "height": 200, "center": [50, 150]}

        res = service.calculate_distance(obj_a, obj_b)
        assert res["success"] is True
        assert res["depth_object_a"] == res["depth_object_b"]

        # Object with no height and no bbox falls back to 100.0
        obj_c = {"class": "car", "center": [50, 150]}
        res_c = service.calculate_distance(obj_c, obj_b)
        assert res_c["success"] is True
        assert res_c["object_a"]["height"] == 100.0

    def test_zero_and_negative_height_clamping(self):
        """Zero or negative height is safely clamped to max(1.0, h), preventing ZeroDivisionError."""
        service = DistanceEstimatorService()
        obj_zero_h = {"class": "car", "height": 0, "center": [200, 200]}
        obj_neg_h = {"class": "car", "height": -50, "center": [400, 200]}

        res = service.calculate_distance(obj_zero_h, obj_neg_h)
        assert res["success"] is True
        assert res["depth_object_a"] > 0
        assert res["depth_object_b"] > 0

    def test_missing_and_invalid_image_dimensions_fallback(self):
        """None or empty image_dimensions dictionary falls back to 960x600 defaults."""
        service = DistanceEstimatorService()
        obj = {"class": "car", "height": 100, "center": [300, 200]}

        res_none = service.calculate_distance(obj, obj, image_dimensions=None)
        res_empty = service.calculate_distance(obj, obj, image_dimensions={})
        res_invalid = service.calculate_distance(obj, obj, image_dimensions="not_a_dict")

        assert res_none["success"] is True
        assert res_empty["success"] is True
        assert res_invalid["success"] is True
        # Default img_w is 960, so adaptive focal length is 960 * 0.9 = 864.0
        assert res_none["focal_length_px"] == 864.0

    def test_adaptive_focal_length_fallback(self):
        """None, zero, or negative focal length triggers adaptive focal length 0.9 * width."""
        service = DistanceEstimatorService()
        obj = {"class": "car", "height": 100, "center": [300, 200]}
        dims = {"width": 1200, "height": 800}

        res_none = service.calculate_distance(obj, obj, image_dimensions=dims, focal_length_px=None)
        res_zero = service.calculate_distance(obj, obj, image_dimensions=dims, focal_length_px=0)
        res_neg = service.calculate_distance(obj, obj, image_dimensions=dims, focal_length_px=-500)

        expected_focal = round(1200 * 0.9, 1) # 1080.0
        assert res_none["focal_length_px"] == expected_focal
        assert res_zero["focal_length_px"] == expected_focal
        assert res_neg["focal_length_px"] == expected_focal

    def test_draw_distance_measurement_valid_base64(self, sample_base64_data_url):
        """Valid base64 image input produces annotated distance measurement visualization."""
        service = DistanceEstimatorService()
        obj_a = {"class": "car", "height": 140, "center": [200, 250], "bbox": [100, 180, 300, 320]}
        obj_b = {"class": "person", "height": 90, "center": [500, 250], "bbox": [470, 205, 530, 295]}

        res = service.calculate_distance(
            object_a=obj_a,
            object_b=obj_b,
            image_dimensions={"width": 640, "height": 480},
            base_image_base64=sample_base64_data_url
        )

        assert res["success"] is True
        assert res["visualization_image"] is not None
        assert res["visualization_image"].startswith("data:image/jpeg;base64,")

    def test_draw_distance_measurement_corrupted_base64(self):
        """Corrupted base64 returns visualization_image: null without crashing."""
        service = DistanceEstimatorService()
        obj_a = {"class": "car", "height": 100, "center": [200, 200]}
        obj_b = {"class": "car", "height": 100, "center": [400, 200]}

        res = service.calculate_distance(
            object_a=obj_a,
            object_b=obj_b,
            base_image_base64="INVALID_CORRUPT_BASE64_STRING!@#$%"
        )

        assert res["success"] is True
        assert res["visualization_image"] is None

    def test_optical_bench_analytical_ground_truth(self, optical_bench_calibrated_pair):
        """Analytical ground truth optical bench test matches within 0.5% tolerance."""
        service = DistanceEstimatorService()
        bench = optical_bench_calibrated_pair

        res = service.calculate_distance(
            object_a=bench["object_a"],
            object_b=bench["object_b"],
            image_dimensions=bench["image_dimensions"],
            focal_length_px=bench["focal_length_px"],
            custom_ref_height_a=1.00,
            custom_ref_height_b=1.00
        )

        assert res["success"] is True
        # Ground truth depths
        assert abs(res["depth_object_a"] - bench["ground_truth_z_a"]) / bench["ground_truth_z_a"] < 0.005
        assert abs(res["depth_object_b"] - bench["ground_truth_z_b"]) / bench["ground_truth_z_b"] < 0.005
        # Ground truth 3D distance
        assert abs(res["distance_3d_meters"] - bench["ground_truth_distance_3d"]) / bench["ground_truth_distance_3d"] < 0.005
