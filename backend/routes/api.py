import os
import json
import cv2
from flask import Blueprint, request, jsonify, current_app
from backend.services.yolo_detector import YOLODetectorService
from backend.services.distance_estimator import DistanceEstimatorService
from backend.utils.image_utils import (
    validate_image_file, file_to_cv2, base64_to_cv2, cv2_to_base64, generate_sample_traffic_scene
)
from backend.utils.sample_data import PROJECT_METADATA

api_bp = Blueprint("api", __name__)

detector_service = None
distance_service = None

def get_detector():
    global detector_service
    if detector_service is None:
        model_name = current_app.config.get("YOLO_MODEL_NAME", "yolov8n.pt")
        detector_service = YOLODetectorService(model_name=model_name)
    return detector_service

def get_distance_estimator():
    global distance_service
    if distance_service is None:
        distance_service = DistanceEstimatorService()
    return distance_service

@api_bp.route("/health", methods=["GET"])
def health_check():
    import os
    detector = get_detector()
    # Sanitize: only expose the filename, never the full system path
    safe_model_name = os.path.basename(detector.model_name) if detector.model_name else None
    return jsonify({
        "status": "healthy",
        "service": "YOLO-Based Object Detection and Distance Measurement API",
        "yolo_loaded": detector.is_loaded,
        "model_name": safe_model_name,
        "load_error": detector.load_error,
        "domain": PROJECT_METADATA["domain"]
    }), 200

@api_bp.route("/detect", methods=["POST"])
def detect_objects():
    try:
        json_data = {}
        form_data = request.form or {}

        is_json_request = request.mimetype == "application/json" or (
            request.content_type and "application/json" in request.content_type
        )

        if is_json_request:
            raw_body = request.get_data(as_text=True)
            if not raw_body or not raw_body.strip():
                return jsonify({"error": "Empty JSON payload"}), 400
            try:
                parsed = json.loads(raw_body)
                if not isinstance(parsed, dict):
                    return jsonify({"error": "JSON payload must be an object"}), 400
                json_data = parsed
            except Exception as e:
                return jsonify({"error": f"Invalid JSON payload: {str(e)}"}), 400
        else:
            parsed = request.get_json(silent=True)
            if isinstance(parsed, dict):
                json_data = parsed

        # Validate conf threshold
        raw_conf = form_data.get("conf") if "conf" in form_data else json_data.get("conf")
        if raw_conf is not None:
            try:
                conf = float(raw_conf)
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid 'conf' threshold '{raw_conf}': must be a numeric value"}), 400
            if not (0.0 <= conf <= 1.0):
                return jsonify({"error": f"Confidence threshold must be between 0.0 and 1.0, got {conf}"}), 400
        else:
            conf = float(current_app.config.get("DEFAULT_CONF_THRESHOLD", 0.25))

        # Validate iou threshold
        raw_iou = form_data.get("iou") if "iou" in form_data else json_data.get("iou")
        if raw_iou is not None:
            try:
                iou = float(raw_iou)
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid 'iou' threshold '{raw_iou}': must be a numeric value"}), 400
            if not (0.0 <= iou <= 1.0):
                return jsonify({"error": f"IOU threshold must be between 0.0 and 1.0, got {iou}"}), 400
        else:
            iou = float(current_app.config.get("DEFAULT_IOU_THRESHOLD", 0.45))

        cv_img = None
        filename = "image.jpg"

        if "image" in request.files:
            file_storage = request.files["image"]
            valid, msg = validate_image_file(file_storage, current_app.config.get("ALLOWED_EXTENSIONS", {"jpg", "jpeg", "png", "webp"}))
            if not valid:
                return jsonify({"error": msg}), 400
            filename = file_storage.filename
            try:
                cv_img = file_to_cv2(file_storage)
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
            except Exception as e:
                return jsonify({"error": f"Failed to read image file: {str(e)}"}), 400
        elif "image_base64" in json_data:
            b64_data = json_data.get("image_base64")
            if not b64_data or not isinstance(b64_data, str) or not b64_data.strip():
                return jsonify({"error": "Field 'image_base64' is empty or invalid"}), 400
            try:
                cv_img = base64_to_cv2(b64_data)
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
            except Exception as e:
                return jsonify({"error": f"Failed to decode base64 image: {str(e)}"}), 400
            filename = json_data.get("filename", "camera_capture.jpg")
        else:
            return jsonify({"error": "No image provided. Upload a file via multipart form-data ('image') or pass 'image_base64' in JSON body."}), 400

        if cv_img is None or cv_img.size == 0:
            return jsonify({"error": "Unable to decode provided image (unsupported format or corrupted data)"}), 400

        detector = get_detector()
        result = detector.detect(cv_img, conf_threshold=conf, iou_threshold=iou)
        result["filename"] = filename
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Detection failed: {str(e)}"}), 500

@api_bp.route("/distance", methods=["POST"])
def calculate_distance():
    raw_body = request.get_data(as_text=True)
    if not raw_body or not raw_body.strip():
        return jsonify({"error": "Empty request body. JSON payload is required."}), 400

    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON payload: {str(e)}"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    obj_a = data.get("object_a")
    obj_b = data.get("object_b")

    if not obj_a or not isinstance(obj_a, dict):
        return jsonify({"error": "Missing or invalid 'object_a': must be a non-empty object"}), 400
    if not obj_b or not isinstance(obj_b, dict):
        return jsonify({"error": "Missing or invalid 'object_b': must be a non-empty object"}), 400

    dims = data.get("image_dimensions")
    if dims is not None and not isinstance(dims, dict):
        return jsonify({"error": "Field 'image_dimensions' must be a dictionary with 'width' and 'height'"}), 400

    focal_px = data.get("focal_length_px")
    if focal_px is not None:
        try:
            focal_px = float(focal_px)
            if focal_px <= 0:
                return jsonify({"error": "Field 'focal_length_px' must be greater than 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid 'focal_length_px' '{focal_px}': must be numeric"}), 400

    img_base64 = data.get("image_base64")
    if img_base64 is not None and not isinstance(img_base64, str):
        return jsonify({"error": "Field 'image_base64' must be a string"}), 400

    custom_ref_a = data.get("custom_ref_height_a")
    if custom_ref_a is not None:
        try:
            custom_ref_a = float(custom_ref_a)
            if custom_ref_a <= 0:
                return jsonify({"error": "Field 'custom_ref_height_a' must be greater than 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid 'custom_ref_height_a' '{custom_ref_a}': must be numeric"}), 400

    custom_ref_b = data.get("custom_ref_height_b")
    if custom_ref_b is not None:
        try:
            custom_ref_b = float(custom_ref_b)
            if custom_ref_b <= 0:
                return jsonify({"error": "Field 'custom_ref_height_b' must be greater than 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid 'custom_ref_height_b' '{custom_ref_b}': must be numeric"}), 400

    try:
        estimator = get_distance_estimator()
        res = estimator.calculate_distance(
            object_a=obj_a,
            object_b=obj_b,
            image_dimensions=dims,
            base_image_base64=img_base64,
            focal_length_px=focal_px,
            custom_ref_height_a=custom_ref_a,
            custom_ref_height_b=custom_ref_b
        )
        return jsonify(res), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Distance calculation failed: {str(e)}"}), 500
