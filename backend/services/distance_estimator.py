import math
import base64
import cv2
import numpy as np

CLASS_REFERENCE_HEIGHTS = {
    "person": 1.70, "bicycle": 1.00, "car": 1.50, "motorcycle": 1.10,
    "bus": 3.20, "train": 3.80, "truck": 3.00, "traffic light": 2.80,
    "chair": 0.85, "bottle": 0.25, "forklift": 2.20
}
DEFAULT_REFERENCE_HEIGHT = 1.50

class DistanceEstimatorService:
    def __init__(self):
        pass

    def calculate_distance(
        self,
        object_a,
        object_b,
        image_dimensions=None,
        base_image_base64=None,
        focal_length_px=None,
        custom_ref_height_a=None,
        custom_ref_height_b=None
    ):
        if not isinstance(image_dimensions, dict):
            image_dimensions = {}

        try:
            img_w = float(image_dimensions.get("width") or 0)
            if img_w <= 0:
                img_w = 960.0
        except (ValueError, TypeError):
            img_w = 960.0

        try:
            img_h = float(image_dimensions.get("height") or 0)
            if img_h <= 0:
                img_h = 600.0
        except (ValueError, TypeError):
            img_h = 600.0

        try:
            focal_val = float(focal_length_px) if focal_length_px is not None else None
            if focal_val is None or focal_val <= 0:
                focal_length_px = round(img_w * 0.9, 1)
            else:
                focal_length_px = focal_val
        except (ValueError, TypeError):
            focal_length_px = round(img_w * 0.9, 1)

        def extract_center(obj):
            if not isinstance(obj, dict):
                return 0.0, 0.0
            if "center" in obj and isinstance(obj["center"], (list, tuple)) and len(obj["center"]) >= 2:
                try:
                    return float(obj["center"][0]), float(obj["center"][1])
                except (ValueError, TypeError):
                    pass
            if "centroid" in obj and isinstance(obj["centroid"], dict):
                try:
                    return float(obj["centroid"].get("x", 0)), float(obj["centroid"].get("y", 0))
                except (ValueError, TypeError):
                    pass
            bbox = obj.get("bbox") or obj.get("box_coords")
            if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                try:
                    return (float(bbox[0]) + float(bbox[2])) / 2.0, (float(bbox[1]) + float(bbox[3])) / 2.0
                except (ValueError, TypeError):
                    pass
            return 0.0, 0.0

        def extract_dim(obj, key, fallback_indices=None):
            if not isinstance(obj, dict):
                return 100.0
            val = obj.get(key)
            if val is not None:
                try:
                    num = float(val)
                    if num > 0:
                        return num
                except (ValueError, TypeError):
                    pass
            bbox = obj.get("bbox") or obj.get("box_coords")
            if bbox and isinstance(bbox, (list, tuple)) and len(bbox) >= 4 and fallback_indices:
                try:
                    i1, i2 = fallback_indices
                    diff = abs(float(bbox[i2]) - float(bbox[i1]))
                    if diff > 0:
                        return diff
                except (ValueError, TypeError):
                    pass
            return 100.0

        cx1, cy1 = extract_center(object_a)
        cx2, cy2 = extract_center(object_b)

        w1 = extract_dim(object_a, "width", (0, 2))
        h1 = extract_dim(object_a, "height", (1, 3))
        w2 = extract_dim(object_b, "width", (0, 2))
        h2 = extract_dim(object_b, "height", (1, 3))

        delta_x = cx2 - cx1
        delta_y = cy2 - cy1
        pixel_distance = math.sqrt(delta_x**2 + delta_y**2)

        img_diagonal = math.sqrt(img_w**2 + img_h**2)
        norm_distance_pct = (pixel_distance / (img_diagonal or 1.0)) * 100.0

        class_a = str(object_a.get("class_name") or object_a.get("class") or "").lower() if isinstance(object_a, dict) else ""
        class_b = str(object_b.get("class_name") or object_b.get("class") or "").lower() if isinstance(object_b, dict) else ""

        def resolve_ref_h(custom_val, cls_name):
            if custom_val is not None:
                try:
                    val = float(custom_val)
                    if val > 0:
                        return val
                except (ValueError, TypeError):
                    pass
            return CLASS_REFERENCE_HEIGHTS.get(cls_name, DEFAULT_REFERENCE_HEIGHT)

        ref_h_a = resolve_ref_h(custom_ref_height_a, class_a)
        ref_h_b = resolve_ref_h(custom_ref_height_b, class_b)

        # Monocular depth: Z = (f * H_real) / h_pixels
        z1 = (focal_length_px * ref_h_a) / max(1.0, h1)
        z2 = (focal_length_px * ref_h_b) / max(1.0, h2)

        c_img_x = img_w / 2.0
        c_img_y = img_h / 2.0

        x1_cam = ((cx1 - c_img_x) * z1) / focal_length_px
        y1_cam = ((cy1 - c_img_y) * z1) / focal_length_px
        x2_cam = ((cx2 - c_img_x) * z2) / focal_length_px
        y2_cam = ((cy2 - c_img_y) * z2) / focal_length_px

        dist_3d_meters = math.sqrt((x2_cam - x1_cam)**2 + (y2_cam - y1_cam)**2 + (z2 - z1)**2)

        distance_visual_base64 = None
        if base_image_base64:
            distance_visual_base64 = self._draw_distance_measurement(
                base_image_base64, object_a, object_b, pixel_distance, dist_3d_meters
            )

        name_a = class_a or (object_a.get("class") if isinstance(object_a, dict) else None) or "object"
        name_b = class_b or (object_b.get("class") if isinstance(object_b, dict) else None) or "object"

        return {
            "success": True,
            "depth_object_a": round(z1, 2),
            "depth_object_b": round(z2, 2),
            "distance_3d_meters": round(dist_3d_meters, 2),
            "pixel_distance": round(pixel_distance, 1),
            "normalized_distance_pct": round(norm_distance_pct, 1),
            "focal_length_px": focal_length_px,
            "object_a": {
                "id": object_a.get("id", "obj_1") if isinstance(object_a, dict) else "obj_1",
                "class_name": name_a,
                "class": name_a,
                "center": [cx1, cy1],
                "bbox": object_a.get("bbox") or object_a.get("box_coords", []) if isinstance(object_a, dict) else [],
                "width": round(w1, 1),
                "height": round(h1, 1),
                "estimated_depth_z": round(z1, 2)
            },
            "object_b": {
                "id": object_b.get("id", "obj_2") if isinstance(object_b, dict) else "obj_2",
                "class_name": name_b,
                "class": name_b,
                "center": [cx2, cy2],
                "bbox": object_b.get("bbox") or object_b.get("box_coords", []) if isinstance(object_b, dict) else [],
                "width": round(w2, 1),
                "height": round(h2, 1),
                "estimated_depth_z": round(z2, 2)
            },
            "metrics": {
                "pixel_distance_px": round(pixel_distance, 1),
                "pixel_distance": round(pixel_distance, 1),
                "delta_x_pixels": round(abs(delta_x), 1),
                "delta_y_pixels": round(abs(delta_y), 1),
                "normalized_distance_pct": round(norm_distance_pct, 1),
                "estimated_relative_distance_m": round(dist_3d_meters, 2),
                "focal_length_px": focal_length_px,
                "disclaimer": "Estimated relative distance using 2D geometric and monocular perspective projection calculations based on detected bounding-box coordinates and camera parameters."
            },
            "visualization_image": distance_visual_base64
        }

    def _draw_distance_measurement(self, image_base64, obj_a, obj_b, px_dist, m_dist):
        try:
            if not isinstance(image_base64, str):
                return None
            clean_b64 = image_base64
            if "," in clean_b64:
                parts = clean_b64.split(",", 1)
                clean_b64 = parts[1] if len(parts) > 1 else ""
            if not clean_b64.strip():
                return None
            img_data = base64.b64decode(clean_b64)
            if not img_data:
                return None
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return None

            def extract_c(obj):
                if not isinstance(obj, dict):
                    return 0, 0
                if "center" in obj and isinstance(obj["center"], (list, tuple)) and len(obj["center"]) >= 2:
                    try:
                        return int(obj["center"][0]), int(obj["center"][1])
                    except (ValueError, TypeError):
                        pass
                if "centroid" in obj and isinstance(obj["centroid"], dict):
                    try:
                        return int(obj["centroid"].get("x", 0)), int(obj["centroid"].get("y", 0))
                    except (ValueError, TypeError):
                        pass
                bbox = obj.get("bbox") or obj.get("box_coords")
                if bbox and isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    try:
                        return int((float(bbox[0]) + float(bbox[2])) / 2), int((float(bbox[1]) + float(bbox[3])) / 2)
                    except (ValueError, TypeError):
                        pass
                return 0, 0

            cx1, cy1 = extract_c(obj_a)
            cx2, cy2 = extract_c(obj_b)

            cv2.line(img, (cx1, cy1), (cx2, cy2), (0, 0, 0), 4, cv2.LINE_AA)
            cv2.line(img, (cx1, cy1), (cx2, cy2), (0, 230, 255), 2, cv2.LINE_AA)

            for cx, cy, label in [(cx1, cy1, "A"), (cx2, cy2, "B")]:
                cv2.circle(img, (cx, cy), 10, (0, 0, 0), -1, cv2.LINE_AA)
                cv2.circle(img, (cx, cy), 8, (0, 230, 255), -1, cv2.LINE_AA)
                cv2.circle(img, (cx, cy), 3, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.putText(img, label, (cx - 4, cy - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

            mid_x = int((cx1 + cx2) / 2)
            mid_y = int((cy1 + cy2) / 2)
            
            badge_text = f"Est: {round(m_dist, 2)}m ({int(px_dist)}px)"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            pad = 6
            cv2.rectangle(img, (mid_x - int(tw / 2) - pad, mid_y - int(th / 2) - pad), (mid_x + int(tw / 2) + pad, mid_y + int(th / 2) + pad), (15, 23, 42), -1)
            cv2.rectangle(img, (mid_x - int(tw / 2) - pad, mid_y - int(th / 2) - pad), (mid_x + int(tw / 2) + pad, mid_y + int(th / 2) + pad), (0, 230, 255), 1)
            cv2.putText(img, badge_text, (mid_x - int(tw / 2), mid_y + int(th / 2) - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)

            _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            return "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            print(f"[DistanceEstimatorService] Error: {e}")
            return None
