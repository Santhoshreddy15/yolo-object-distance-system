"""Unit tests for YOLODetectorService (backend/services/yolo_detector.py).

Tests model loading, input format compatibility (numpy, PIL, file path),
confidence/IoU filtering, schema integrity, and fallback mechanisms.
"""

import os
import tempfile
import pytest
import numpy as np
import cv2
from PIL import Image

from backend.services.yolo_detector import YOLODetectorService
from backend.config import Config


class TestYOLODetectorService:
    """Unit tests for YOLO detector service."""

    def test_detector_initialization_default(self):
        """Service initializes with configured model name and reports load status."""
        model_path = Config.YOLO_MODEL_NAME
        service = YOLODetectorService(model_name=model_path)
        assert service.model_name == model_path
        # Ultralytics model should be loaded or load_error recorded
        assert isinstance(service.is_loaded, bool)
        if not service.is_loaded:
            assert service.load_error is not None

    def test_detector_initialization_invalid_model(self):
        """Service handles invalid model path gracefully without crashing."""
        service = YOLODetectorService(model_name="nonexistent_model_weights_12345.pt")
        assert service.model_name == "nonexistent_model_weights_12345.pt"
        assert service.is_loaded is False
        assert service.load_error is not None

    def test_detector_detect_numpy_ndarray(self):
        """Detector accepts standard OpenCV BGR numpy array."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Draw some features
        cv2.rectangle(img, (100, 100), (300, 300), (200, 50, 50), -1)

        result = service.detect(img)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "model_used" in result
        assert "inference_time_ms" in result
        assert result["inference_time_ms"] >= 0.0
        assert result["image_dimensions"] == {"width": 640, "height": 480}
        assert isinstance(result["detections"], list)
        assert isinstance(result["total_objects"], int)
        assert result["total_objects"] == len(result["detections"])
        assert "original_image" in result
        assert result["original_image"].startswith("data:image/jpeg;base64,")
        assert "annotated_image" in result
        assert result["annotated_image"].startswith("data:image/jpeg;base64,")

    def test_detector_detect_pil_image(self):
        """Detector accepts PIL Image object and converts to proper color space."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        pil_img = Image.new("RGB", (320, 240), color=(120, 80, 40))

        result = service.detect(pil_img)
        assert result["success"] is True
        assert result["image_dimensions"] == {"width": 320, "height": 240}
        assert isinstance(result["detections"], list)

    def test_detector_detect_file_path(self):
        """Detector accepts valid image file path on disk."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            temp_path = tf.name
            canvas = np.full((300, 400, 3), 128, dtype=np.uint8)
            cv2.imwrite(temp_path, canvas)

        try:
            result = service.detect(temp_path)
            assert result["success"] is True
            assert result["image_dimensions"] == {"width": 400, "height": 300}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_detector_detect_unsupported_input_type(self):
        """Detector raises TypeError when passed unsupported input types."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        with pytest.raises(TypeError, match="Unsupported image format"):
            service.detect(12345)

        with pytest.raises(TypeError, match="Unsupported image format"):
            service.detect(["not", "an", "image"])

        with pytest.raises(TypeError, match="Unsupported image format"):
            service.detect(None)

    def test_detector_detect_nonexistent_file_path(self):
        """Detector raises ValueError when passed a non-existent file path."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        with pytest.raises(ValueError, match="Could not read image from path"):
            service.detect("nonexistent_path_xyz_987654.jpg")

    def test_detector_confidence_threshold_filtering(self):
        """Confidence threshold parameter controls detection sensitivity."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        canvas = np.full((480, 640, 3), 100, dtype=np.uint8)

        # Detect with standard vs extremely high threshold
        res_standard = service.detect(canvas, conf_threshold=0.25)
        res_high_conf = service.detect(canvas, conf_threshold=0.99)

        assert res_standard["success"] is True
        assert res_high_conf["success"] is True
        # High confidence threshold should return fewer or equal detections
        assert len(res_high_conf["detections"]) <= len(res_standard["detections"])

    def test_detector_iou_threshold_parameter(self):
        """IoU threshold parameter is accepted and executed cleanly."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        canvas = np.full((480, 640, 3), 80, dtype=np.uint8)

        result = service.detect(canvas, iou_threshold=0.30)
        assert result["success"] is True
        assert isinstance(result["detections"], list)

    def test_detector_detection_field_schema(self):
        """Detections list items contain all required contract fields with expected types."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        # Use fallback generator to test exact schema structure hermetically
        detections = service._generate_fallback_detections(width=800, height=600)

        assert len(detections) >= 2
        for d in detections:
            assert isinstance(d["id"], str)
            assert isinstance(d["index"], int)
            assert isinstance(d["class_name"], str)
            assert isinstance(d["class_id"], int)
            assert isinstance(d["confidence"], float)
            assert isinstance(d["confidence_pct"], float)
            assert isinstance(d["bbox"], list) and len(d["bbox"]) == 4
            assert isinstance(d["center"], list) and len(d["center"]) == 2
            assert isinstance(d["width"], int) and d["width"] > 0
            assert isinstance(d["height"], int) and d["height"] > 0
            assert isinstance(d["bottom_center"], list) and len(d["bottom_center"]) == 2

    def test_detector_bounding_box_clamping(self):
        """Bounding boxes are clamped within image dimensions."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        w, h = 640, 480
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        result = service.detect(canvas)

        for d in result["detections"]:
            x1, y1, x2, y2 = d["bbox"]
            assert 0 <= x1 <= w - 1
            assert 0 <= y1 <= h - 1
            assert 0 <= x2 <= w - 1
            assert 0 <= y2 <= h - 1

    def test_detector_render_annotations(self):
        """_render_annotations draws bounding boxes and text without altering image size."""
        service = YOLODetectorService(model_name=Config.YOLO_MODEL_NAME)
        img = np.full((400, 500, 3), 60, dtype=np.uint8)
        dummy_dets = [
            {
                "bbox": [50, 50, 200, 250],
                "center": [125, 150],
                "class_name": "car",
                "confidence_pct": 92.5,
                "class_id": 2
            }
        ]
        annotated = service._render_annotations(img.copy(), dummy_dets)
        assert isinstance(annotated, np.ndarray)
        assert annotated.shape == img.shape
        assert annotated.dtype == img.dtype
        # The annotated image should have modified pixel values where drawn
        assert not np.array_equal(annotated, img)
