"""Unit tests for image processing utilities (backend/utils/image_utils.py).

Tests file validation, format checking, file-to-cv2 decoding, base64 encoding/decoding,
0-byte rejection, corrupted payload handling, and synthetic scene generation.
"""

import os
import io
import tempfile
import pytest
import numpy as np
import cv2
from werkzeug.datastructures import FileStorage

from backend.utils.image_utils import (
    validate_image_file,
    file_to_cv2,
    base64_to_cv2,
    cv2_to_base64,
    generate_sample_traffic_scene
)


class TestImageUtils:
    """Unit tests for backend/utils/image_utils.py."""

    ALLOWED = {"jpg", "jpeg", "png", "webp"}

    # ---------------------------------------------------------
    # validate_image_file
    # ---------------------------------------------------------
    def test_validate_image_file_valid_extensions(self, sample_jpeg_bytes, sample_png_bytes, sample_webp_bytes):
        """All supported formats (.jpg, .jpeg, .png, .webp) pass file validation."""
        for name, data in [
            ("test.jpg", sample_jpeg_bytes),
            ("test.jpeg", sample_jpeg_bytes),
            ("test.png", sample_png_bytes),
            ("test.webp", sample_webp_bytes),
        ]:
            fs = FileStorage(stream=io.BytesIO(data), filename=name)
            valid, msg = validate_image_file(fs, self.ALLOWED)
            assert valid is True
            assert msg == name.rsplit(".", 1)[-1].lower()

    def test_validate_image_file_invalid_extensions(self):
        """Disallowed extensions (.exe, .sh, .txt, .zip, .bin) are rejected."""
        for invalid_name in ["script.sh", "payload.exe", "readme.txt", "archive.zip", "data.bin"]:
            fs = FileStorage(stream=io.BytesIO(b"fake data"), filename=invalid_name)
            valid, msg = validate_image_file(fs, self.ALLOWED)
            assert valid is False
            assert "Unsupported file extension" in msg

    def test_validate_image_file_no_extension(self):
        """Files without extension are rejected with descriptive error."""
        fs = FileStorage(stream=io.BytesIO(b"data"), filename="image_without_extension")
        valid, msg = validate_image_file(fs, self.ALLOWED)
        assert valid is False
        assert "Unsupported file extension" in msg

    def test_validate_image_file_none_or_missing(self):
        """None or file storage without filename returns False."""
        valid, msg = validate_image_file(None, self.ALLOWED)
        assert valid is False
        assert msg == "No file provided"

        fs = FileStorage(stream=io.BytesIO(b"data"), filename="")
        valid2, msg2 = validate_image_file(fs, self.ALLOWED)
        assert valid2 is False
        assert msg2 == "No file provided"

    def test_validate_image_file_zero_bytes(self):
        """0-byte file storage is rejected early."""
        fs = FileStorage(stream=io.BytesIO(b""), filename="empty.jpg")
        valid, msg = validate_image_file(fs, self.ALLOWED)
        assert valid is False
        assert "empty (0 bytes)" in msg

    # ---------------------------------------------------------
    # file_to_cv2
    # ---------------------------------------------------------
    def test_file_to_cv2_valid(self, sample_jpeg_bytes):
        """Valid file storage decodes to valid OpenCV BGR image."""
        fs = FileStorage(stream=io.BytesIO(sample_jpeg_bytes), filename="car.jpg")
        cv_img = file_to_cv2(fs)
        assert isinstance(cv_img, np.ndarray)
        assert cv_img.shape[2] == 3
        assert cv_img.size > 0

    def test_file_to_cv2_none_storage(self):
        """None file storage raises ValueError."""
        with pytest.raises(ValueError, match="No file storage provided"):
            file_to_cv2(None)

    def test_file_to_cv2_zero_bytes(self):
        """0-byte stream raises ValueError."""
        fs = FileStorage(stream=io.BytesIO(b""), filename="empty.jpg")
        with pytest.raises(ValueError, match="empty \\(0 bytes\\)"):
            file_to_cv2(fs)

    def test_file_to_cv2_corrupt_bytes(self, sample_corrupt_bytes):
        """Corrupted non-image bytes raise ValueError."""
        fs = FileStorage(stream=io.BytesIO(sample_corrupt_bytes), filename="corrupt.jpg")
        with pytest.raises(ValueError, match="Could not decode image"):
            file_to_cv2(fs)

    # ---------------------------------------------------------
    # base64_to_cv2
    # ---------------------------------------------------------
    def test_base64_to_cv2_valid_data_url(self, sample_base64_data_url):
        """Standard JPEG Data URL Base64 decodes cleanly."""
        cv_img = base64_to_cv2(sample_base64_data_url)
        assert isinstance(cv_img, np.ndarray)
        assert cv_img.ndim == 3
        assert cv_img.size > 0

    def test_base64_to_cv2_valid_png_data_url(self, sample_png_data_url):
        """Standard PNG Data URL Base64 decodes cleanly."""
        cv_img = base64_to_cv2(sample_png_data_url)
        assert isinstance(cv_img, np.ndarray)
        assert cv_img.size > 0

    def test_base64_to_cv2_valid_raw_base64(self, sample_raw_base64):
        """Raw Base64 string without data URL prefix decodes cleanly."""
        cv_img = base64_to_cv2(sample_raw_base64)
        assert isinstance(cv_img, np.ndarray)
        assert cv_img.size > 0

    def test_base64_to_cv2_whitespace_handling(self, sample_base64_data_url):
        """Leading/trailing whitespace and newlines are stripped and decoded cleanly."""
        padded_b64 = f"  \n\t{sample_base64_data_url} \t\n "
        cv_img = base64_to_cv2(padded_b64)
        assert isinstance(cv_img, np.ndarray)
        assert cv_img.size > 0

    def test_base64_to_cv2_none_or_non_string(self):
        """None or non-string input raises ValueError."""
        with pytest.raises(ValueError, match="missing or not a string"):
            base64_to_cv2(None)

        with pytest.raises(ValueError, match="missing or not a string"):
            base64_to_cv2(12345)

    def test_base64_to_cv2_empty_string(self):
        """Empty or whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            base64_to_cv2("")

        with pytest.raises(ValueError, match="empty"):
            base64_to_cv2("   \n\t ")

    def test_base64_to_cv2_data_url_prefix_without_payload(self):
        """Data URL prefix without payload raises ValueError."""
        with pytest.raises(ValueError, match="prefix but no payload"):
            base64_to_cv2("data:image/jpeg;base64,")

    def test_base64_to_cv2_corrupted_characters(self):
        """Corrupted Base64 characters raise ValueError."""
        with pytest.raises(ValueError):
            base64_to_cv2("not_valid_base64_chars!@#$%^&*()_+==")

    def test_base64_to_cv2_valid_base64_non_image_payload(self):
        """Base64 that decodes to non-image bytes raises ValueError."""
        import base64
        b64_text = base64.b64encode(b"This is just plain text, not an image format.").decode("utf-8")
        with pytest.raises(ValueError, match="Unable to decode image from base64"):
            base64_to_cv2(b64_text)

    # ---------------------------------------------------------
    # cv2_to_base64
    # ---------------------------------------------------------
    def test_cv2_to_base64_valid(self):
        """Valid numpy array encodes to data URL string."""
        img = np.full((100, 100, 3), 128, dtype=np.uint8)
        b64_jpg = cv2_to_base64(img, format_ext=".jpg")
        assert b64_jpg.startswith("data:image/jpeg;base64,")

        b64_png = cv2_to_base64(img, format_ext=".png")
        assert b64_png.startswith("data:image/png;base64,")

    def test_cv2_to_base64_invalid_inputs(self):
        """None, non-array, or 0-size image returns empty string."""
        assert cv2_to_base64(None) == ""
        assert cv2_to_base64("not_an_array") == ""
        assert cv2_to_base64(np.array([])) == ""

    # ---------------------------------------------------------
    # generate_sample_traffic_scene
    # ---------------------------------------------------------
    def test_generate_sample_traffic_scene(self):
        """Generates standard calibrated traffic scene on disk with 960x600 resolution."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            out_path = tf.name

        try:
            res_path = generate_sample_traffic_scene(out_path)
            assert os.path.exists(res_path)
            img = cv2.imread(res_path)
            assert img is not None
            assert img.shape == (600, 960, 3)
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)
