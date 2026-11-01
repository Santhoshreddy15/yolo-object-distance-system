"""Tier 3: Cross-Feature Combinations E2E Tests.

Validates pairwise feature interactions, end-to-end workflows, and format invariance:
- Pipeline: /api/detect -> extract detected objects -> /api/distance
- Multi-class pairwise distance: Car/Person, Bus/Bicycle, Truck/Motorcycle, Forklift/Person
- Invariance: 5 input formats (JPEG, PNG, WEBP, Data URL Base64, Raw Base64)
- Geometric Laws: Focal length scaling property, Distance symmetry (D(A,B) == D(B,A))
- Flexible Object Contracts: center, centroid dict, and bbox coordinates
"""

import io
import math
import pytest
from e2e_tests.conftest import create_synthetic_image


def test_combo_detect_then_distance_full_pipeline(client, sample_jpeg_bytes):
    """C1: End-to-end pipeline: POST /api/detect -> extract objects -> POST /api/distance."""
    # Step 1: Detect objects in image
    detect_resp = client.post(
        "/api/detect",
        data={"image": (io.BytesIO(sample_jpeg_bytes), "traffic.jpg")},
        content_type="multipart/form-data"
    )
    assert detect_resp.status_code == 200
    detect_data = detect_resp.get_json()
    assert detect_data.get("success") is True
    detections = detect_data.get("detections", [])
    if len(detections) >= 2:
        obj_a = detections[0]
        obj_b = detections[1]
    else:
        obj_a = {
            "id": "obj_1",
            "class_name": "car",
            "height": 140,
            "width": 260,
            "center": [270.0, 430.0],
            "bbox": [140, 360, 400, 500]
        }
        obj_b = {
            "id": "obj_2",
            "class_name": "car",
            "height": 110,
            "width": 210,
            "center": [685.0, 365.0],
            "bbox": [580, 310, 790, 420]
        }

    # Step 2: Feed extracted detections and original image into /api/distance
    dist_payload = {
        "object_a": obj_a,
        "object_b": obj_b,
        "image_dimensions": detect_data["image_dimensions"],
        "image_base64": detect_data["original_image"],
        "focal_length_px": 800.0
    }
    dist_resp = client.post("/api/distance", json=dist_payload)
    assert dist_resp.status_code == 200, f"Distance step failed: {dist_resp.data}"
    dist_data = dist_resp.get_json()

    assert dist_data.get("success") is True
    assert dist_data["metrics"]["estimated_relative_distance_m"] > 0.0
    assert dist_data.get("visualization_image") is not None
    assert dist_data["visualization_image"].startswith("data:image/jpeg;base64,")


def test_combo_pairwise_classes_vehicle_and_pedestrian(client):
    """C2: Pairwise interaction between car (1.50m) and person (1.70m)."""
    f = 800.0
    payload = {
        "object_a": {
            "id": "car_1",
            "class_name": "car",
            "height": 150,
            "center": [250.0, 350.0],
            "bbox": [150, 275, 350, 425]
        },
        "object_b": {
            "id": "person_1",
            "class_name": "person",
            "height": 170,
            "center": [550.0, 350.0],
            "bbox": [525, 265, 575, 435]
        },
        "image_dimensions": {"width": 800, "height": 600},
        "focal_length_px": f
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    # Z = (f * H) / h
    # Car: (800 * 1.50) / 150 = 8.00m
    # Person: (800 * 1.70) / 170 = 8.00m
    z_car = data["object_a"]["estimated_depth_z"]
    z_person = data["object_b"]["estimated_depth_z"]

    assert abs(z_car - 8.00) < 0.1, f"Car depth {z_car} != 8.00"
    assert abs(z_person - 8.00) < 0.1, f"Person depth {z_person} != 8.00"


def test_combo_pairwise_classes_heavy_vehicle_and_two_wheeler(client):
    """C3: Pairwise interaction between bus (3.20m) and bicycle (1.00m)."""
    f = 800.0
    payload = {
        "object_a": {
            "id": "bus_1",
            "class_name": "bus",
            "height": 320,
            "center": [300.0, 300.0],
            "bbox": [150, 140, 450, 460]
        },
        "object_b": {
            "id": "bike_1",
            "class_name": "bicycle",
            "height": 100,
            "center": [600.0, 400.0],
            "bbox": [550, 350, 650, 450]
        },
        "image_dimensions": {"width": 1000, "height": 800},
        "focal_length_px": f
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    # Both objects have pixel height corresponding to exact 8.0m depth:
    # Bus: (800 * 3.20) / 320 = 8.00m
    # Bike: (800 * 1.00) / 100 = 8.00m
    z_bus = data["object_a"]["estimated_depth_z"]
    z_bike = data["object_b"]["estimated_depth_z"]
    assert abs(z_bus - 8.00) < 0.1
    assert abs(z_bike - 8.00) < 0.1


def test_combo_pairwise_forklift_and_worker(client, synthetic_forklift_pair):
    """C4: Industrial warehouse safety scenario: Forklift vs Worker distance."""
    response = client.post("/api/distance", json=synthetic_forklift_pair)
    assert response.status_code == 200
    data = response.get_json()

    assert data.get("success") is True
    metrics = data["metrics"]
    rel_dist = metrics["estimated_relative_distance_m"]
    # Distance in 3D should be positive and bounded realistically
    assert 1.0 < rel_dist < 20.0, f"Relative warehouse distance {rel_dist} out of bounds"


def test_combo_format_invariance_detection_across_all_5_modes(client):
    """C5: System produces valid detections across all 5 supported ingestion formats."""
    w, h = 640, 480
    jpeg_bytes = create_synthetic_image("JPEG", w, h)
    png_bytes = create_synthetic_image("PNG", w, h)
    webp_bytes = create_synthetic_image("WEBP", w, h)

    import base64
    raw_b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    data_url_b64 = f"data:image/jpeg;base64,{raw_b64}"

    results = []

    # 1. Multipart JPEG
    r1 = client.post("/api/detect", data={"image": (io.BytesIO(jpeg_bytes), "test.jpg")}, content_type="multipart/form-data")
    assert r1.status_code == 200
    results.append(r1.get_json())

    # 2. Multipart PNG
    r2 = client.post("/api/detect", data={"image": (io.BytesIO(png_bytes), "test.png")}, content_type="multipart/form-data")
    assert r2.status_code == 200
    results.append(r2.get_json())

    # 3. Multipart WEBP
    r3 = client.post("/api/detect", data={"image": (io.BytesIO(webp_bytes), "test.webp")}, content_type="multipart/form-data")
    assert r3.status_code == 200
    results.append(r3.get_json())

    # 4. JSON Data URL
    r4 = client.post("/api/detect", json={"image_base64": data_url_b64})
    assert r4.status_code == 200
    results.append(r4.get_json())

    # 5. JSON Raw Base64
    r5 = client.post("/api/detect", json={"image_base64": raw_b64})
    assert r5.status_code == 200
    results.append(r5.get_json())

    # Verify dimension consistency across all 5 ingestion pathways
    for idx, res in enumerate(results):
        dims = res["image_dimensions"]
        assert dims["width"] == w, f"Format {idx} width mismatch: {dims['width']}"
        assert dims["height"] == h, f"Format {idx} height mismatch: {dims['height']}"


def test_combo_focal_length_linear_scaling_property(client, synthetic_car_pair):
    """C6: Depth estimation scales linearly with focal length: Z(2f) == 2 * Z(f)."""
    p1 = dict(synthetic_car_pair)
    p1["focal_length_px"] = 500.0

    p2 = dict(synthetic_car_pair)
    p2["focal_length_px"] = 1000.0 # Exactly 2x

    r1 = client.post("/api/distance", json=p1)
    r2 = client.post("/api/distance", json=p2)
    assert r1.status_code == 200 and r2.status_code == 200

    z1 = r1.get_json()["object_a"]["estimated_depth_z"]
    z2 = r2.get_json()["object_a"]["estimated_depth_z"]

    scaling_ratio = z2 / z1
    assert abs(scaling_ratio - 2.0) < 0.05, f"Expected 2.0 scaling ratio, got {scaling_ratio}"


def test_combo_distance_symmetry_and_depth_ordering(client, synthetic_car_pair):
    """C7: Euclidean distance is symmetric: D(A, B) == D(B, A)."""
    payload_ab = dict(synthetic_car_pair)
    payload_ba = {
        "object_a": synthetic_car_pair["object_b"],
        "object_b": synthetic_car_pair["object_a"],
        "image_dimensions": synthetic_car_pair["image_dimensions"],
        "focal_length_px": synthetic_car_pair["focal_length_px"]
    }

    resp_ab = client.post("/api/distance", json=payload_ab)
    resp_ba = client.post("/api/distance", json=payload_ba)
    assert resp_ab.status_code == 200 and resp_ba.status_code == 200

    d_ab = resp_ab.get_json()["metrics"]["estimated_relative_distance_m"]
    d_ba = resp_ba.get_json()["metrics"]["estimated_relative_distance_m"]

    assert abs(d_ab - d_ba) < 1e-4, f"Distance asymmetry: D(A,B)={d_ab} != D(B,A)={d_ba}"

    px_ab = resp_ab.get_json()["metrics"]["pixel_distance"]
    px_ba = resp_ba.get_json()["metrics"]["pixel_distance"]
    assert abs(px_ab - px_ba) < 1e-4


def test_combo_rapid_consecutive_interleaved_pipeline(client, sample_jpeg_bytes, synthetic_car_pair):
    """C8: Interleaving 10 consecutive detect and distance requests causes no state leakage."""
    for i in range(5):
        # Detect request
        r_det = client.post(
            "/api/detect",
            data={"image": (io.BytesIO(sample_jpeg_bytes), f"frame_{i}.jpg")},
            content_type="multipart/form-data"
        )
        assert r_det.status_code == 200

        # Distance request
        r_dist = client.post("/api/distance", json=synthetic_car_pair)
        assert r_dist.status_code == 200


def test_combo_distance_with_centroid_and_bbox_formats(client):
    """C9: Distance service accepts objects specified with centroid dict or bbox array."""
    f = 800.0
    payload = {
        "object_a": {
            "id": "obj_dict_centroid",
            "class_name": "car",
            "height": 100,
            "width": 200,
            "centroid": {"x": 300, "y": 400}
        },
        "object_b": {
            "id": "obj_bbox_only",
            "class_name": "car",
            "height": 100,
            "width": 200,
            "bbox": [500, 350, 700, 450] # center is [600, 400]
        },
        "image_dimensions": {"width": 1000, "height": 800},
        "focal_length_px": f
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    # dx = 600 - 300 = 300, dy = 400 - 400 = 0 -> pixel_distance = 300.0
    px_dist = data["metrics"]["pixel_distance"]
    assert abs(px_dist - 300.0) < 1.0, f"Expected pixel distance 300.0, got {px_dist}"


def test_combo_distance_height_boundary_scaling(client):
    """C10: Smaller pixel height corresponds to greater depth (perspective foreshortening)."""
    f = 800.0
    payload = {
        "object_a": {"class_name": "car", "height": 200, "center": [300, 400]},
        "object_b": {"class_name": "car", "height": 100, "center": [600, 400]},
        "focal_length_px": f
    }
    response = client.post("/api/distance", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    z_a = data["object_a"]["estimated_depth_z"]
    z_b = data["object_b"]["estimated_depth_z"]

    # Object with half the pixel height (100 vs 200) must have double the depth
    assert z_b > z_a
    assert abs((z_b / z_a) - 2.0) < 0.05
