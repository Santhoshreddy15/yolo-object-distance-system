import os
import cv2
import numpy as np
import base64
from PIL import Image
import io

def validate_image_file(file_storage, allowed_extensions):
    if not file_storage or not getattr(file_storage, "filename", None):
        return False, "No file provided"
    filename = file_storage.filename.lower()
    ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    if not ext or ext not in allowed_extensions:
        allowed_str = ", ".join(sorted(allowed_extensions))
        return False, f"Unsupported file extension '.{ext}'. Allowed: {allowed_str}"
    try:
        file_storage.seek(0, os.SEEK_END)
        size = file_storage.tell()
        file_storage.seek(0)
        if size == 0:
            return False, "Uploaded image file is empty (0 bytes)"
    except Exception:
        pass
    return True, ext

def file_to_cv2(file_storage):
    if not file_storage:
        raise ValueError("No file storage provided")
    try:
        file_storage.seek(0)
        raw_bytes = file_storage.read()
    except Exception as e:
        raise ValueError(f"Could not read uploaded file: {str(e)}")

    if not raw_bytes or len(raw_bytes) == 0:
        raise ValueError("Uploaded image file is empty (0 bytes)")

    np_arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    if np_arr.size == 0:
        raise ValueError("Uploaded file contains no byte data")

    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image from file bytes: unsupported or corrupted image format")
    return image

def base64_to_cv2(base64_str):
    if base64_str is None or not isinstance(base64_str, str):
        raise ValueError("Base64 image string is missing or not a string")

    clean_str = base64_str.strip()
    if not clean_str:
        raise ValueError("Base64 image string is empty")

    if "," in clean_str:
        parts = clean_str.split(",", 1)
        clean_str = parts[1].strip() if len(parts) > 1 else ""
        if not clean_str:
            raise ValueError("Base64 string contains data URL prefix but no payload")

    try:
        data = base64.b64decode(clean_str, validate=True)
    except Exception:
        try:
            data = base64.b64decode(clean_str)
        except Exception as err:
            raise ValueError(f"Corrupted or invalid base64 encoding: {str(err)}")

    if not data or len(data) == 0:
        raise ValueError("Decoded base64 image data is empty (0 bytes)")

    np_arr = np.frombuffer(data, dtype=np.uint8)
    if np_arr.size == 0:
        raise ValueError("Decoded base64 data contains no bytes")

    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image from base64 payload: unsupported or corrupted format")
    return image

def cv2_to_base64(image, format_ext=".jpg", quality=90):
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return ""
    ext = format_ext if format_ext.startswith(".") else f".{format_ext}"
    success, buffer = cv2.imencode(ext, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        raise ValueError(f"Failed to encode image to {ext}")
    b64_str = base64.b64encode(buffer).decode("utf-8")
    mime = "jpeg" if ext.lower() in [".jpg", ".jpeg"] else "png"
    return f"data:image/{mime};base64,{b64_str}"

def generate_sample_traffic_scene(output_path):
    width, height = 960, 600
    canvas = np.full((height, width, 3), (35, 30, 25), dtype=np.uint8)

    for y in range(int(height * 0.45)):
        ratio = y / (height * 0.45)
        b = int(140 + ratio * 40)
        g = int(100 + ratio * 30)
        r = int(70 + ratio * 20)
        canvas[y, :] = (b, g, r)

    road_pts = np.array([
        [0, height],
        [width, height],
        [int(width * 0.7), int(height * 0.45)],
        [int(width * 0.3), int(height * 0.45)]
    ], np.int32)
    cv2.fillPoly(canvas, [road_pts], (45, 45, 45))
    cv2.line(canvas, (int(width * 0.5), int(height * 0.45)), (int(width * 0.4), height), (220, 220, 220), 4)

    # Car 1
    c1_x, c1_y, c1_w, c1_h = 140, 360, 260, 140
    cv2.rectangle(canvas, (c1_x, c1_y + 40), (c1_x + c1_w, c1_y + c1_h), (180, 50, 40), -1)
    cv2.circle(canvas, (c1_x + 50, c1_y + c1_h), 28, (20, 20, 20), -1)
    cv2.circle(canvas, (c1_x + c1_w - 50, c1_y + c1_h), 28, (20, 20, 20), -1)

    # Car 2
    c2_x, c2_y, c2_w, c2_h = 580, 310, 210, 110
    cv2.rectangle(canvas, (c2_x, c2_y + 30), (c2_x + c2_w, c2_y + c2_h), (30, 140, 200), -1)
    cv2.circle(canvas, (c2_x + 40, c2_y + c2_h), 22, (20, 20, 20), -1)
    cv2.circle(canvas, (c2_x + c2_w - 40, c2_y + c2_h), 22, (20, 20, 20), -1)

    cv2.imwrite(output_path, canvas)
    return output_path
