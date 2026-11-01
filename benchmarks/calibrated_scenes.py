"""Programmatic Calibrated Reference Scenes for Accuracy & Distance Benchmarking.

Generates calibrated reference scenes using OpenCV and NumPy with mathematically
known ground-truth 3D camera coordinates, bounding boxes, object heights, and
relative 3D Euclidean distances.
"""

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import cv2
import numpy as np


@dataclass
class GroundTruthObject:
    """Ground truth object annotation in camera space."""
    id: str
    class_name: str
    bbox: List[int]  # [x1, y1, x2, y2]
    width: int
    height: int
    center: Tuple[float, float]
    real_height_m: float
    depth_z_m: float
    camera_coords_3d: Tuple[float, float, float]  # (X, Y, Z) in meters


@dataclass
class GroundTruthDistancePair:
    """Calibrated pair of objects with ground-truth relative 3D separation."""
    pair_id: str
    object_a_id: str
    object_b_id: str
    ground_truth_distance_3d_m: float
    ground_truth_pixel_distance: float
    ground_truth_norm_pct: float
    tolerance_pct: float = 5.0  # Max acceptable percentage error (<5% standard, <0.5% optical)


@dataclass
class CalibratedScene:
    """A calibrated evaluation scene containing image and analytical ground truth."""
    name: str
    description: str
    filename: str
    width: int
    height: int
    focal_length_px: float
    objects: List[GroundTruthObject]
    distance_pairs: List[GroundTruthDistancePair]
    image_path: Optional[Path] = None

    def get_object(self, obj_id: str) -> Optional[GroundTruthObject]:
        for obj in self.objects:
            if obj.id == obj_id:
                return obj
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "focal_length_px": self.focal_length_px,
            "objects_count": len(self.objects),
            "pairs_count": len(self.distance_pairs),
            "objects": [
                {
                    "id": obj.id,
                    "class_name": obj.class_name,
                    "bbox": obj.bbox,
                    "width": obj.width,
                    "height": obj.height,
                    "center": list(obj.center),
                    "real_height_m": obj.real_height_m,
                    "depth_z_m": obj.depth_z_m,
                    "camera_coords_3d": list(obj.camera_coords_3d),
                }
                for obj in self.objects
            ],
            "distance_pairs": [
                {
                    "pair_id": p.pair_id,
                    "object_a_id": p.object_a_id,
                    "object_b_id": p.object_b_id,
                    "ground_truth_distance_3d_m": p.ground_truth_distance_3d_m,
                    "ground_truth_pixel_distance": p.ground_truth_pixel_distance,
                    "tolerance_pct": p.tolerance_pct,
                }
                for p in self.distance_pairs
            ],
        }


def _compute_camera_projection(
    cx: float, cy: float, h_px: float, real_h_m: float,
    img_w: int, img_h: int, focal_px: float
) -> Tuple[float, float, float]:
    """Calculate monocular projective depth Z and camera (X, Y, Z) in meters."""
    z = (focal_px * real_h_m) / max(1.0, float(h_px))
    c_img_x = img_w / 2.0
    c_img_y = img_h / 2.0
    x = ((cx - c_img_x) * z) / focal_px
    y = ((cy - c_img_y) * z) / focal_px
    return round(x, 4), round(y, 4), round(z, 4)


def _compute_euclidean_distance_3d(
    coords_a: Tuple[float, float, float], coords_b: Tuple[float, float, float]
) -> float:
    """Calculate Euclidean separation between two 3D camera coordinates."""
    dx = coords_b[0] - coords_a[0]
    dy = coords_b[1] - coords_a[1]
    dz = coords_b[2] - coords_a[2]
    return round(math.sqrt(dx * dx + dy * dy + dz * dz), 4)


class CalibratedSceneRegistry:
    """Registry and generator for programmatic calibrated benchmark scenes."""

    def __init__(self, output_dir: Optional[Path] = None):
        if output_dir is None:
            output_dir = Path(__file__).resolve().parent / "reference_data"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scenes: Dict[str, CalibratedScene] = {}
        self._build_scenes()

    def _build_scenes(self):
        """Construct analytical metadata and generate programmatic scene images."""
        self._build_urban_traffic_scene()
        self._build_warehouse_logistics_scene()
        self._build_optical_bench_scene()
        self._build_pedestrian_crosswalk_scene()

    def _build_urban_traffic_scene(self):
        """Scene 1: Urban Traffic Scene ($960 \\times 600$, $f=864.0$ px)."""
        w, h = 960, 600
        focal_px = 864.0  # 0.9 * 960

        # Car 1 (Lead Vehicle)
        c1_bbox = [140, 360, 400, 500]
        c1_w = c1_bbox[2] - c1_bbox[0]  # 260
        c1_h = c1_bbox[3] - c1_bbox[1]  # 140
        c1_cx = (c1_bbox[0] + c1_bbox[2]) / 2.0  # 270.0
        c1_cy = (c1_bbox[1] + c1_bbox[3]) / 2.0  # 430.0
        c1_real_h = 1.50
        c1_x, c1_y, c1_z = _compute_camera_projection(c1_cx, c1_cy, c1_h, c1_real_h, w, h, focal_px)

        # Car 2 (Trailing Vehicle)
        c2_bbox = [580, 310, 790, 420]
        c2_w = c2_bbox[2] - c2_bbox[0]  # 210
        c2_h = c2_bbox[3] - c2_bbox[1]  # 110
        c2_cx = (c2_bbox[0] + c2_bbox[2]) / 2.0  # 685.0
        c2_cy = (c2_bbox[1] + c2_bbox[3]) / 2.0  # 365.0
        c2_real_h = 1.50
        c2_x, c2_y, c2_z = _compute_camera_projection(c2_cx, c2_cy, c2_h, c2_real_h, w, h, focal_px)

        obj_a = GroundTruthObject(
            id="car_lead",
            class_name="car",
            bbox=c1_bbox,
            width=c1_w,
            height=c1_h,
            center=(c1_cx, c1_cy),
            real_height_m=c1_real_h,
            depth_z_m=c1_z,  # ~9.26m
            camera_coords_3d=(c1_x, c1_y, c1_z),
        )
        obj_b = GroundTruthObject(
            id="car_trail",
            class_name="car",
            bbox=c2_bbox,
            width=c2_w,
            height=c2_h,
            center=(c2_cx, c2_cy),
            real_height_m=c2_real_h,
            depth_z_m=c2_z,  # ~11.78m
            camera_coords_3d=(c2_x, c2_y, c2_z),
        )

        dist_3d = _compute_euclidean_distance_3d((c1_x, c1_y, c1_z), (c2_x, c2_y, c2_z))  # ~5.66m
        px_dist = round(math.sqrt((c2_cx - c1_cx) ** 2 + (c2_cy - c1_cy) ** 2), 2)  # 420.1px
        diag = math.sqrt(w * w + h * h)
        norm_pct = round((px_dist / diag) * 100.0, 2)

        pair = GroundTruthDistancePair(
            pair_id="car_lead_vs_car_trail",
            object_a_id="car_lead",
            object_b_id="car_trail",
            ground_truth_distance_3d_m=dist_3d,
            ground_truth_pixel_distance=px_dist,
            ground_truth_norm_pct=norm_pct,
            tolerance_pct=5.0,
        )

        img_path = self.output_dir / "traffic_urban.jpg"
        self._render_traffic_urban_image(img_path, w, h, c1_bbox, c2_bbox)

        self.scenes["traffic_urban"] = CalibratedScene(
            name="traffic_urban",
            description="Urban Traffic Scene with Car 1 (depth 9.26m) and Car 2 (depth 11.78m)",
            filename="traffic_urban.jpg",
            width=w,
            height=h,
            focal_length_px=focal_px,
            objects=[obj_a, obj_b],
            distance_pairs=[pair],
            image_path=img_path,
        )

    def _build_warehouse_logistics_scene(self):
        """Scene 2: Warehouse Logistics Scene ($1280 \\times 720$, $f=920.0$ px)."""
        w, h = 1280, 720
        focal_px = 920.0

        # Forklift
        fk_bbox = [230, 250, 410, 470]
        fk_w = fk_bbox[2] - fk_bbox[0]  # 180
        fk_h = fk_bbox[3] - fk_bbox[1]  # 220
        fk_cx = (fk_bbox[0] + fk_bbox[2]) / 2.0  # 320.0
        fk_cy = (fk_bbox[1] + fk_bbox[3]) / 2.0  # 360.0
        fk_real_h = 2.20
        fk_x, fk_y, fk_z = _compute_camera_projection(fk_cx, fk_cy, fk_h, fk_real_h, w, h, focal_px)

        # Worker (Person)
        wk_bbox = [545, 240, 615, 520]
        wk_w = wk_bbox[2] - wk_bbox[0]  # 70
        wk_h = wk_bbox[3] - wk_bbox[1]  # 280
        wk_cx = (wk_bbox[0] + wk_bbox[2]) / 2.0  # 580.0
        wk_cy = (wk_bbox[1] + wk_bbox[3]) / 2.0  # 380.0
        wk_real_h = 1.70
        wk_x, wk_y, wk_z = _compute_camera_projection(wk_cx, wk_cy, wk_h, wk_real_h, w, h, focal_px)

        obj_a = GroundTruthObject(
            id="forklift_unit_1",
            class_name="forklift",
            bbox=fk_bbox,
            width=fk_w,
            height=fk_h,
            center=(fk_cx, fk_cy),
            real_height_m=fk_real_h,
            depth_z_m=fk_z,  # 9.20m
            camera_coords_3d=(fk_x, fk_y, fk_z),
        )
        obj_b = GroundTruthObject(
            id="worker_pedestrian_1",
            class_name="person",
            bbox=wk_bbox,
            width=wk_w,
            height=wk_h,
            center=(wk_cx, wk_cy),
            real_height_m=wk_real_h,
            depth_z_m=wk_z,  # 5.59m
            camera_coords_3d=(wk_x, wk_y, wk_z),
        )

        dist_3d = _compute_euclidean_distance_3d((fk_x, fk_y, fk_z), (wk_x, wk_y, wk_z))  # ~4.60m
        px_dist = round(math.sqrt((wk_cx - fk_cx) ** 2 + (wk_cy - fk_cy) ** 2), 2)
        diag = math.sqrt(w * w + h * h)
        norm_pct = round((px_dist / diag) * 100.0, 2)

        pair = GroundTruthDistancePair(
            pair_id="forklift_vs_worker",
            object_a_id="forklift_unit_1",
            object_b_id="worker_pedestrian_1",
            ground_truth_distance_3d_m=dist_3d,
            ground_truth_pixel_distance=px_dist,
            ground_truth_norm_pct=norm_pct,
            tolerance_pct=5.0,
        )

        img_path = self.output_dir / "warehouse_logistics.jpg"
        self._render_warehouse_image(img_path, w, h, fk_bbox, wk_bbox)

        self.scenes["warehouse_logistics"] = CalibratedScene(
            name="warehouse_logistics",
            description="Industrial Warehouse Logistics Scene with Forklift (H=2.20m) and Worker (H=1.70m)",
            filename="warehouse_logistics.jpg",
            width=w,
            height=h,
            focal_length_px=focal_px,
            objects=[obj_a, obj_b],
            distance_pairs=[pair],
            image_path=img_path,
        )

    def _build_optical_bench_scene(self):
        """Scene 3: Optical Bench Calibration Targets ($1000 \\times 800$, $f=800.0$ px)."""
        w, h = 1000, 800
        focal_px = 800.0

        # Analytical Targets using standard default reference height H=1.50m
        # Target A: h=160px -> Z = (800 * 1.50) / 160 = 7.50m
        t1_bbox = [450, 320, 550, 480]
        t1_w = t1_bbox[2] - t1_bbox[0]  # 100
        t1_h = t1_bbox[3] - t1_bbox[1]  # 160
        t1_cx = (t1_bbox[0] + t1_bbox[2]) / 2.0  # 500.0
        t1_cy = (t1_bbox[1] + t1_bbox[3]) / 2.0  # 400.0
        t1_real_h = 1.50
        t1_x, t1_y, t1_z = _compute_camera_projection(t1_cx, t1_cy, t1_h, t1_real_h, w, h, focal_px)

        # Target B: h=80px -> Z = (800 * 1.50) / 80 = 15.00m
        t2_bbox = [475, 260, 525, 340]
        t2_w = t2_bbox[2] - t2_bbox[0]  # 50
        t2_h = t2_bbox[3] - t2_bbox[1]  # 80
        t2_cx = (t2_bbox[0] + t2_bbox[2]) / 2.0  # 500.0
        t2_cy = (t2_bbox[1] + t2_bbox[3]) / 2.0  # 300.0
        t2_real_h = 1.50
        t2_x, t2_y, t2_z = _compute_camera_projection(t2_cx, t2_cy, t2_h, t2_real_h, w, h, focal_px)

        obj_a = GroundTruthObject(
            id="target_7_5m",
            class_name="car",  # Standard prior 1.50m
            bbox=t1_bbox,
            width=t1_w,
            height=t1_h,
            center=(t1_cx, t1_cy),
            real_height_m=t1_real_h,
            depth_z_m=t1_z,  # 7.50m
            camera_coords_3d=(t1_x, t1_y, t1_z),
        )
        obj_b = GroundTruthObject(
            id="target_15m",
            class_name="car",  # Standard prior 1.50m
            bbox=t2_bbox,
            width=t2_w,
            height=t2_h,
            center=(t2_cx, t2_cy),
            real_height_m=t2_real_h,
            depth_z_m=t2_z,  # 15.00m
            camera_coords_3d=(t2_x, t2_y, t2_z),
        )

        dist_3d = _compute_euclidean_distance_3d((t1_x, t1_y, t1_z), (t2_x, t2_y, t2_z))  # ~7.73m
        px_dist = round(math.sqrt((t2_cx - t1_cx) ** 2 + (t2_cy - t1_cy) ** 2), 2)  # 100.0px
        diag = math.sqrt(w * w + h * h)
        norm_pct = round((px_dist / diag) * 100.0, 2)

        pair = GroundTruthDistancePair(
            pair_id="target_near_vs_far",
            object_a_id="target_7_5m",
            object_b_id="target_15m",
            ground_truth_distance_3d_m=dist_3d,
            ground_truth_pixel_distance=px_dist,
            ground_truth_norm_pct=norm_pct,
            tolerance_pct=0.5,  # Mathematically bounded tolerance < 0.5%
        )

        img_path = self.output_dir / "optical_bench.jpg"
        self._render_optical_bench_image(img_path, w, h, t1_bbox, t2_bbox)

        self.scenes["optical_bench"] = CalibratedScene(
            name="optical_bench",
            description="Optical Bench Calibration Targets (depth error tolerance < 0.5%)",
            filename="optical_bench.jpg",
            width=w,
            height=h,
            focal_length_px=focal_px,
            objects=[obj_a, obj_b],
            distance_pairs=[pair],
            image_path=img_path,
        )

    def _build_pedestrian_crosswalk_scene(self):
        """Scene 4: Pedestrian Crosswalk Scene ($1000 \\times 800$, $f=800.0$ px)."""
        w, h = 1000, 800
        focal_px = 800.0

        # Pedestrian Left: H=1.70m, h=170px -> Z = 8.00m
        p1_bbox = [270, 365, 330, 535]
        p1_w = p1_bbox[2] - p1_bbox[0]  # 60
        p1_h = p1_bbox[3] - p1_bbox[1]  # 170
        p1_cx = (p1_bbox[0] + p1_bbox[2]) / 2.0  # 300.0
        p1_cy = (p1_bbox[1] + p1_bbox[3]) / 2.0  # 450.0
        p1_real_h = 1.70
        p1_x, p1_y, p1_z = _compute_camera_projection(p1_cx, p1_cy, p1_h, p1_real_h, w, h, focal_px)

        # Pedestrian Right: H=1.70m, h=170px -> Z = 8.00m
        p2_bbox = [670, 365, 730, 535]
        p2_w = p2_bbox[2] - p2_bbox[0]  # 60
        p2_h = p2_bbox[3] - p2_bbox[1]  # 170
        p2_cx = (p2_bbox[0] + p2_bbox[2]) / 2.0  # 700.0
        p2_cy = (p2_bbox[1] + p2_bbox[3]) / 2.0  # 450.0
        p2_real_h = 1.70
        p2_x, p2_y, p2_z = _compute_camera_projection(p2_cx, p2_cy, p2_h, p2_real_h, w, h, focal_px)

        obj_a = GroundTruthObject(
            id="ped_left",
            class_name="person",
            bbox=p1_bbox,
            width=p1_w,
            height=p1_h,
            center=(p1_cx, p1_cy),
            real_height_m=p1_real_h,
            depth_z_m=p1_z,  # 8.00m
            camera_coords_3d=(p1_x, p1_y, p1_z),
        )
        obj_b = GroundTruthObject(
            id="ped_right",
            class_name="person",
            bbox=p2_bbox,
            width=p2_w,
            height=p2_h,
            center=(p2_cx, p2_cy),
            real_height_m=p2_real_h,
            depth_z_m=p2_z,  # 8.00m
            camera_coords_3d=(p2_x, p2_y, p2_z),
        )

        dist_3d = _compute_euclidean_distance_3d((p1_x, p1_y, p1_z), (p2_x, p2_y, p2_z))  # 4.00m pure lateral
        px_dist = round(math.sqrt((p2_cx - p1_cx) ** 2 + (p2_cy - p1_cy) ** 2), 2)  # 400.0px
        diag = math.sqrt(w * w + h * h)
        norm_pct = round((px_dist / diag) * 100.0, 2)

        pair = GroundTruthDistancePair(
            pair_id="ped_left_vs_ped_right",
            object_a_id="ped_left",
            object_b_id="ped_right",
            ground_truth_distance_3d_m=dist_3d,
            ground_truth_pixel_distance=px_dist,
            ground_truth_norm_pct=norm_pct,
            tolerance_pct=5.0,
        )

        img_path = self.output_dir / "pedestrian_crosswalk.jpg"
        self._render_crosswalk_image(img_path, w, h, p1_bbox, p2_bbox)

        self.scenes["pedestrian_crosswalk"] = CalibratedScene(
            name="pedestrian_crosswalk",
            description="Pedestrian Crosswalk Scene (lateral Delta X separation = 4.00m)",
            filename="pedestrian_crosswalk.jpg",
            width=w,
            height=h,
            focal_length_px=focal_px,
            objects=[obj_a, obj_b],
            distance_pairs=[pair],
            image_path=img_path,
        )

    # -------------------------------------------------------------------------
    # Programmatic Image Generators
    # -------------------------------------------------------------------------

    def _render_traffic_urban_image(self, path: Path, width: int, height: int, b1: List[int], b2: List[int]):
        """Render high-fidelity urban traffic scene."""
        img = np.full((height, width, 3), (35, 30, 25), dtype=np.uint8)

        # Sky gradient
        sky_h = int(height * 0.45)
        for y in range(sky_h):
            r = y / sky_h
            img[y, :] = (int(140 + r * 40), int(100 + r * 30), int(70 + r * 20))

        # Buildings in background
        cv2.rectangle(img, (20, 100), (180, sky_h), (60, 50, 45), -1)
        cv2.rectangle(img, (200, 60), (380, sky_h), (80, 70, 60), -1)
        cv2.rectangle(img, (750, 80), (920, sky_h), (70, 60, 55), -1)

        # Road surface
        road_pts = np.array([
            [0, height],
            [width, height],
            [int(width * 0.72), sky_h],
            [int(width * 0.28), sky_h]
        ], np.int32)
        cv2.fillPoly(img, [road_pts], (45, 45, 45))

        # Center dashed markings
        for i in range(5):
            y_start = int(sky_h + (height - sky_h) * (i / 5.0) + 10)
            y_end = int(y_start + 25)
            x_mid = int(width * 0.5 - (y_start - sky_h) * 0.15)
            cv2.line(img, (x_mid, y_start), (x_mid, y_end), (220, 220, 220), 4)

        # Vehicle 1 (Red SUV / Lead car)
        x1, y1, x2, y2 = b1
        cv2.rectangle(img, (x1, y1 + 35), (x2, y2), (180, 50, 40), -1)
        cv2.rectangle(img, (x1 + 30, y1), (x2 - 30, y1 + 45), (160, 40, 35), -1)
        # Windows
        cv2.rectangle(img, (x1 + 40, y1 + 10), (x2 - 40, y1 + 40), (220, 210, 190), -1)
        # Wheels
        cv2.circle(img, (x1 + 50, y2), 26, (20, 20, 20), -1)
        cv2.circle(img, (x2 - 50, y2), 26, (20, 20, 20), -1)
        cv2.circle(img, (x1 + 50, y2), 12, (180, 180, 180), -1)
        cv2.circle(img, (x2 - 50, y2), 12, (180, 180, 180), -1)

        # Vehicle 2 (Blue Sedan / Trailing car)
        x1, y1, x2, y2 = b2
        cv2.rectangle(img, (x1, y1 + 25), (x2, y2), (30, 140, 200), -1)
        cv2.rectangle(img, (x1 + 25, y1), (x2 - 25, y1 + 35), (20, 110, 170), -1)
        # Windows
        cv2.rectangle(img, (x1 + 35, y1 + 8), (x2 - 35, y1 + 30), (220, 210, 190), -1)
        # Wheels
        cv2.circle(img, (x1 + 40, y2), 20, (20, 20, 20), -1)
        cv2.circle(img, (x2 - 40, y2), 20, (20, 20, 20), -1)
        cv2.circle(img, (x1 + 40, y2), 9, (180, 180, 180), -1)
        cv2.circle(img, (x2 - 40, y2), 9, (180, 180, 180), -1)

        cv2.imwrite(str(path), img)

    def _render_warehouse_image(self, path: Path, width: int, height: int, b1: List[int], b2: List[int]):
        """Render high-fidelity industrial warehouse logistics scene."""
        img = np.full((height, width, 3), (70, 75, 80), dtype=np.uint8)

        # Floor / Wall horizon
        floor_y = int(height * 0.40)
        cv2.rectangle(img, (0, floor_y), (width, height), (95, 100, 105), -1)

        # Yellow safety floor lines
        cv2.line(img, (100, height), (350, floor_y), (30, 200, 230), 4)
        cv2.line(img, (width - 100, height), (width - 350, floor_y), (30, 200, 230), 4)

        # Warehouse metal racks in background
        for rx in [50, 450, 850]:
            cv2.rectangle(img, (rx, 60), (rx + 250, floor_y + 80), (40, 50, 90), 3)
            for level in [120, 180, 240]:
                cv2.line(img, (rx, level), (rx + 250, level), (40, 50, 90), 3)
                # Storage boxes on racks
                cv2.rectangle(img, (rx + 20, level - 40), (rx + 100, level), (50, 100, 140), -1)
                cv2.rectangle(img, (rx + 120, level - 45), (rx + 220, level), (40, 90, 130), -1)

        # Forklift
        fx1, fy1, fx2, fy2 = b1
        # Yellow body
        cv2.rectangle(img, (fx1 + 40, fy1 + 80), (fx2, fy2 - 20), (20, 180, 230), -1)
        # Overhead cage / cabin
        cv2.rectangle(img, (fx1 + 60, fy1 + 20), (fx2 - 20, fy1 + 80), (30, 30, 30), 4)
        # Mast & Forks
        cv2.line(img, (fx1 + 30, fy1), (fx1 + 30, fy2), (50, 50, 50), 6)
        cv2.line(img, (fx1, fy2 - 10), (fx1 + 30, fy2 - 10), (30, 30, 30), 6)
        # Heavy wheels
        cv2.circle(img, (fx1 + 70, fy2 - 10), 28, (20, 20, 20), -1)
        cv2.circle(img, (fx2 - 30, fy2 - 10), 28, (20, 20, 20), -1)

        # Worker (Person with high-vis vest and hardhat)
        wx1, wy1, wx2, wy2 = b2
        w_mid = int((wx1 + wx2) / 2)
        # Hardhat (Yellow)
        cv2.ellipse(img, (w_mid, wy1 + 20), (16, 12), 0, 0, 360, (20, 210, 240), -1)
        # Face / Head
        cv2.circle(img, (w_mid, wy1 + 35), 14, (140, 175, 215), -1)
        # High-Vis Vest Body
        cv2.rectangle(img, (wx1 + 8, wy1 + 50), (wx2 - 8, wy1 + 160), (30, 215, 245), -1)
        cv2.line(img, (w_mid, wy1 + 50), (w_mid, wy1 + 160), (230, 230, 230), 3)
        # Pants (Navy blue)
        cv2.rectangle(img, (wx1 + 10, wy1 + 160), (wx2 - 10, wy2), (80, 40, 30), -1)

        cv2.imwrite(str(path), img)

    def _render_optical_bench_image(self, path: Path, width: int, height: int, b1: List[int], b2: List[int]):
        """Render optical calibration bench with resolution targets."""
        img = np.full((height, width, 3), (20, 20, 20), dtype=np.uint8)

        # Optical bench grid lines
        for x in range(0, width, 50):
            cv2.line(img, (x, 0), (x, height), (40, 40, 40), 1)
        for y in range(0, height, 50):
            cv2.line(img, (0, y), (width, y), (40, 40, 40), 1)

        # Laser alignment line (Cyan)
        cv2.line(img, (int(width / 2), 0), (int(width / 2), height), (150, 120, 40), 1)

        # Render calibrated target A (Near target)
        x1, y1, x2, y2 = b1
        cv2.rectangle(img, (x1, y1), (x2, y2), (240, 240, 240), -1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 3)
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        # Bullseye circles
        for rad in [60, 45, 30, 15, 5]:
            cv2.circle(img, (cx, cy), rad, (0, 0, 0), 2)
        cv2.line(img, (x1, cy), (x2, cy), (0, 0, 0), 2)
        cv2.line(img, (cx, y1), (cx, y2), (0, 0, 0), 2)

        # Render calibrated target B (Far target)
        x1, y1, x2, y2 = b2
        cv2.rectangle(img, (x1, y1), (x2, y2), (230, 230, 230), -1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 2)
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        for rad in [30, 20, 10, 3]:
            cv2.circle(img, (cx, cy), rad, (0, 0, 0), 1)
        cv2.line(img, (x1, cy), (x2, cy), (0, 0, 0), 1)
        cv2.line(img, (cx, y1), (cx, y2), (0, 0, 0), 1)

        cv2.imwrite(str(path), img)

    def _render_crosswalk_image(self, path: Path, width: int, height: int, b1: List[int], b2: List[int]):
        """Render pedestrian crosswalk scene."""
        img = np.full((height, width, 3), (40, 40, 40), dtype=np.uint8)

        # Crosswalk zebra stripes
        for sx in range(100, width - 100, 120):
            cv2.rectangle(img, (sx, 350), (sx + 70, 560), (220, 220, 220), -1)

        # Pedestrian 1
        x1, y1, x2, y2 = b1
        mid_x = int((x1 + x2) / 2)
        cv2.circle(img, (mid_x, y1 + 20), 16, (140, 175, 215), -1)  # Head
        cv2.rectangle(img, (x1 + 10, y1 + 36), (x2 - 10, y1 + 110), (180, 80, 50), -1)  # Torso
        cv2.line(img, (x1 + 18, y1 + 110), (x1 + 12, y2), (30, 30, 30), 8)  # Leg 1
        cv2.line(img, (x2 - 18, y1 + 110), (x2 - 12, y2), (30, 30, 30), 8)  # Leg 2

        # Pedestrian 2
        x1, y1, x2, y2 = b2
        mid_x = int((x1 + x2) / 2)
        cv2.circle(img, (mid_x, y1 + 20), 16, (140, 175, 215), -1)  # Head
        cv2.rectangle(img, (x1 + 10, y1 + 36), (x2 - 10, y1 + 110), (50, 120, 180), -1)  # Torso
        cv2.line(img, (x1 + 18, y1 + 110), (x1 + 12, y2), (30, 30, 30), 8)  # Leg 1
        cv2.line(img, (x2 - 18, y1 + 110), (x2 - 12, y2), (30, 30, 30), 8)  # Leg 2

        cv2.imwrite(str(path), img)


def get_all_calibrated_scenes(output_dir: Optional[Path] = None) -> Dict[str, CalibratedScene]:
    """Helper returning a loaded registry of all calibrated benchmark scenes."""
    registry = CalibratedSceneRegistry(output_dir=output_dir)
    return registry.scenes
