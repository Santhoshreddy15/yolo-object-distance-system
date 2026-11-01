# Complete API & Calibration Specification Analysis

**Role**: Specification Miner (API & Calibration)  
**Working Directory**: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\spec_miner_survey`  
**Target Repository**: `C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system`  
**Date**: 2026-11-01  
**Status**: Completed  

---

## Executive Summary

This specification mining report delivers the authoritative, exhaustive specification for the REST API endpoints, image ingestion pipelines, camera calibration parameters, pinhole perspective models, and monocular distance estimation equations in the YOLO Object Detection and Distance Estimation System.

All findings are extracted directly through static code inspection of the authoritative backend (`backend/app.py`, `backend/config.py`, `backend/routes/api.py`, `backend/services/distance_estimator.py`, `backend/services/yolo_detector.py`, `backend/utils/image_utils.py`, `backend/utils/sample_data.py`) and frontend integration layer (`frontend/src/services/api.js`, `frontend/src/utils/geometry.js`, `frontend/src/services/mockData.js`, `frontend/src/components/DistanceMeasurementPanel.jsx`).

---

## 1. REST API Specification

### 1.1 Architecture & Network Endpoints Overview

The Flask backend exposes four route paths under CORS-enabled headers (`origins: "*"`):

| Route Path | HTTP Method | Service Component | Content-Type Handled | Purpose |
|------------|-------------|-------------------|----------------------|---------|
| `/` | `GET` | `app.py:index` | None | API Welcome & Service Directory metadata |
| `/api/health` | `GET` | `backend.routes.api:health_check` | None | Service liveness, model load status, domain metadata |
| `/api/detect` | `POST` | `backend.routes.api:detect_objects` | `multipart/form-data`, `application/json` | Runs YOLOv8 inference, extracts bounding boxes, generates annotated visual |
| `/api/distance` | `POST` | `backend.routes.api:calculate_distance` | `application/json` | Computes monocular 3D depth, 2D centroid distance, and composite separation |

---

### 1.2 Route: `GET /` (Service Directory)

- **URL**: `http://<host>:<port>/`
- **Method**: `GET`
- **Headers**: None
- **Query Parameters**: None
- **Request Body**: None
- **Status Code**: `200 OK`
- **Response Format**: `application/json`

#### Response Schema
```json
{
  "project": "YOLO-Based Object Detection and Distance Measurement",
  "domain": "Artificial Intelligence and Computer Vision",
  "api_endpoints": [
    "/api/health",
    "/api/detect (POST)",
    "/api/distance (POST)"
  ],
  "status": "Online"
}
```

---

### 1.3 Route: `GET /api/health` (Liveness & Model Status)

- **URL**: `http://<host>:<port>/api/health`
- **Method**: `GET`
- **Headers**: None
- **Query Parameters**: None
- **Request Body**: None
- **Status Code**: `200 OK`
- **Response Format**: `application/json`

#### Response Schema (Model Successfully Loaded)
```json
{
  "status": "healthy",
  "service": "YOLO-Based Object Detection and Distance Measurement API",
  "yolo_loaded": true,
  "model_name": "yolov8n.pt",
  "load_error": null,
  "domain": "Artificial Intelligence and Computer Vision"
}
```

#### Response Schema (Model Failed to Initialize / Fallback Mode)
```json
{
  "status": "healthy",
  "service": "YOLO-Based Object Detection and Distance Measurement API",
  "yolo_loaded": false,
  "model_name": "yolov8n.pt",
  "load_error": "<Error message / traceback string>",
  "domain": "Artificial Intelligence and Computer Vision"
}
```

---

### 1.4 Route: `POST /api/detect` (Object Detection & Annotation)

- **URL**: `http://<host>:<port>/api/detect`
- **Method**: `POST`
- **CORS Support**: All origins (`*`) on `/api/*`
- **Max Content Length**: 16 MB (`MAX_CONTENT_LENGTH = 16 * 1024 * 1024`)

#### Ingestion Mode A: `multipart/form-data`
Used primarily by standard file upload dialogs:
- `image`: File binary. Permitted extensions: `jpg`, `jpeg`, `png`, `webp` (case-insensitive).
- `conf`: (Optional, string/float) Confidence threshold. Defaults to `0.25` (`Config.DEFAULT_CONF_THRESHOLD`).
- `iou`: (Optional, string/float) IoU threshold for NMS. Defaults to `0.45` (`Config.DEFAULT_IOU_THRESHOLD`).

#### Ingestion Mode B: `application/json`
Used by webcam captures, base64 feeds, and programmatic API clients:
- `image_base64`: (Required) String. Either a Data URL (`data:image/jpeg;base64,<payload>`) or raw Base64 string.
- `filename`: (Optional, string) Defaults to `"camera_capture.jpg"`.
- `conf`: (Optional, float) Confidence threshold (default `0.25`).
- `iou`: (Optional, float) IoU threshold (default `0.45`).

#### Ingestion Mode C: Direct Raw Binary Image
- Currently, sending raw binary with header `Content-Type: image/jpeg` without `multipart/form-data` or `image_base64` fails with `400 Bad Request`: `{"error": "No image provided. Upload a file or pass 'image_base64'."}`.

#### Successful Response Schema (`200 OK`)
```json
{
  "success": true,
  "model_used": "yolov8n.pt",
  "inference_time_ms": 19.45,
  "image_dimensions": {
    "width": 960,
    "height": 600
  },
  "total_objects": 2,
  "detections": [
    {
      "id": "obj_1",
      "index": 1,
      "class_name": "car",
      "class_id": 2,
      "confidence": 0.9412,
      "confidence_pct": 94.1,
      "bbox": [140, 360, 400, 500],
      "center": [270, 430],
      "width": 260,
      "height": 140,
      "bottom_center": [270, 500]
    },
    {
      "id": "obj_2",
      "index": 2,
      "class_name": "person",
      "class_id": 0,
      "confidence": 0.8845,
      "confidence_pct": 88.5,
      "bbox": [580, 310, 790, 420],
      "center": [685, 365],
      "width": 210,
      "height": 110,
      "bottom_center": [685, 420]
    }
  ],
  "original_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "annotated_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "classes_detected": ["car", "person"],
  "filename": "traffic_urban.jpg"
}
```

#### Field Specifications & Value Ranges
- `inference_time_ms`: Float, execution time of image decoding + model forward pass + post-processing in milliseconds.
- `detections[].bbox`: Array of 4 integers `[x1, y1, x2, y2]`, clamped to `[0, width - 1]` and `[0, height - 1]`.
- `detections[].center`: Array of 2 integers `[cx, cy]` where $cx = \lfloor(x1 + x2)/2\rfloor$, $cy = \lfloor(y1 + y2)/2\rfloor$.
- `detections[].bottom_center`: Array of 2 integers `[cx, y2]`. Ground contact point.
- `detections[].confidence`: Float in range `[0.0, 1.0]`, rounded to 4 decimals.
- `detections[].confidence_pct`: Float in range `[0.0, 100.0]`, rounded to 1 decimal.

#### Error Responses
- `400 Bad Request`:
  - Missing image payload: `{"error": "No image provided. Upload a file or pass 'image_base64'."}`
  - Unsupported extension: `{"error": "Unsupported file extension '.bmp'. Allowed: jpg, jpeg, png, webp"}`
  - Empty file upload: `{"error": "No file provided"}`
  - Corrupt / Unreadable image: `{"error": "Unable to decode provided image"}`
- `500 Internal Server Error`:
  - Unhandled exception / YOLO failure: `{"error": "Detection failed: <detail>"}`
- `413 Payload Too Large`:
  - Flask default error when payload exceeds 16 MB.

---

### 1.5 Route: `POST /api/distance` (Monocular 3D Distance Estimation)

- **URL**: `http://<host>:<port>/api/distance`
- **Method**: `POST`
- **Content-Type**: `application/json` (enforced via `request.get_json(force=True)`)

#### Request Payload Schema
```json
{
  "object_a": {
    "id": "obj_1",
    "class_name": "car",
    "bbox": [140, 360, 400, 500],
    "center": [270, 430],
    "width": 260,
    "height": 140
  },
  "object_b": {
    "id": "obj_2",
    "class_name": "person",
    "bbox": [580, 310, 790, 420],
    "center": [685, 365],
    "width": 210,
    "height": 110
  },
  "image_dimensions": {
    "width": 960,
    "height": 600
  },
  "image_base64": "data:image/jpeg;base64,...",
  "focal_length_px": 864.0
}
```

#### Supported Variations in Input Object Coordinates
The backend `extract_center` function supports three distinct formats for object center coordinates:
1. `obj["center"]`: `[cx, cy]` (list or tuple, length $\ge 2$).
2. `obj["centroid"]`: `{"x": cx, "y": cy}` (dictionary).
3. `obj["bbox"]` or `obj["box_coords"]`: `[x1, y1, x2, y2]`. If centroid is omitted, it auto-computes:
   $$cx = \frac{x_1 + x_2}{2}, \quad cy = \frac{y_1 + y_2}{2}$$

#### Successful Response Schema (`200 OK`)
```json
{
  "success": true,
  "object_a": {
    "id": "obj_1",
    "class_name": "car",
    "center": [270.0, 430.0],
    "bbox": [140, 360, 400, 500],
    "estimated_depth_z": 9.26
  },
  "object_b": {
    "id": "obj_2",
    "class_name": "person",
    "center": [685.0, 365.0],
    "bbox": [580, 310, 790, 420],
    "estimated_depth_z": 13.36
  },
  "metrics": {
    "pixel_distance_px": 420.1,
    "pixel_distance": 420.1,
    "delta_x_pixels": 415.0,
    "delta_y_pixels": 65.0,
    "normalized_distance_pct": 37.1,
    "estimated_relative_distance_m": 6.84,
    "focal_length_px": 864.0,
    "disclaimer": "Estimated relative distance using 2D geometric and monocular perspective projection calculations based on detected bounding-box coordinates and camera parameters."
  },
  "visualization_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

#### Units of Measurement
- `pixel_distance_px` / `pixel_distance`: Pixels (`px`), 2D Euclidean distance on the image plane.
- `delta_x_pixels`: Pixels (`px`), $|cx_2 - cx_1|$.
- `delta_y_pixels`: Pixels (`px`), $|cy_2 - cy_1|$.
- `normalized_distance_pct`: Percentage (`%`) of image diagonal ($D_{sensor} = \sqrt{W^2 + H^2}$).
- `estimated_depth_z`: Meters (`m`), perpendicular distance $Z$ from camera sensor to object plane along optical axis.
- `estimated_relative_distance_m`: Meters (`m`), 3D Euclidean distance $D_{3D}$ between the two objects.

#### Error Responses
- `400 Bad Request`:
  - Missing either `object_a` or `object_b`: `{"error": "Both object_a and object_b are required"}`
- `500 Internal Server Error`:
  - Unhandled exception / malformed payload: `{"error": "Distance calculation failed: <detail>"}`

---

## 2. Camera Calibration & Monocular Distance Model Specification

### 2.1 The Mathematical Model

The monocular distance estimation engine relies on a pinhole camera model combined with class-specific anthropomorphic and dimensional geometric priors ($H_{real}$).

```
          Camera Optical Center (0, 0, 0)
                      /|\
                     / | \
                    /  |  \
                   /   |f  \       Image Plane (z = f)
                  /----+----\  <-- Object projection (h_pixels)
                 /     |     \
                /      |      \
               /       |Z      \   Real World Scene
              /--------+--------\ <-- Real Object (H_real)
```

#### Step 1: Pinhole Monocular Depth Equation
From triangle similarity in the pinhole camera model:
$$\frac{h_{pixels}}{f} = \frac{H_{real}}{Z} \implies Z = \frac{f \cdot H_{real}}{h_{pixels}}$$
Where:
- $f$: Camera focal length in pixels (`focal_length_px`).
- $H_{real}$: Known real-world physical height of the object class in meters (class prior).
- $h_{pixels}$: Height of the detected 2D bounding box in pixels (`max(1, height)`).
- $Z$: Estimated depth along the optical camera Z-axis in meters.

#### Step 2: Perspective Back-Projection to 3D Camera Coordinate System
Assuming the optical center (principal point) is located at the geometric center of the sensor:
$$c_{img\_x} = \frac{W}{2}, \quad c_{img\_y} = \frac{H}{2}$$
The 3D coordinates $(X_{cam}, Y_{cam}, Z_{cam})$ of each object centroid in camera space (meters) are:
$$X_{cam} = \frac{(c_x - c_{img\_x}) \cdot Z}{f}$$
$$Y_{cam} = \frac{(c_y - c_{img\_y}) \cdot Z}{f}$$
$$Z_{cam} = Z$$

#### Step 3: 3D Relative Separation (Euclidean Distance in Camera Space)
The relative spatial separation $D_{3D}$ between Object A and Object B is:
$$D_{3D} = \sqrt{(X_{cam2} - X_{cam1})^2 + (Y_{cam2} - Y_{cam1})^2 + (Z_2 - Z_1)^2}$$
Units: Meters (`m`), rounded to 2 decimal places.

#### Step 4: 2D Pixel Metrics
- Centroid Euclidean Distance:
  $$\Delta x = cx_2 - cx_1, \quad \Delta y = cy_2 - cy_1$$
  $$D_{pixel} = \sqrt{\Delta x^2 + \Delta y^2}$$
- Image Sensor Diagonal:
  $$D_{diag} = \sqrt{W^2 + H^2}$$
- Normalized Distance Percentage:
  $$D_{norm\%} = \left(\frac{D_{pixel}}{D_{diag}}\right) \times 100\%$$

---

### 2.2 Calibration Parameters & Defaults

#### Focal Length ($f$)
- Default configuration parameter: `DEFAULT_FOCAL_LENGTH_PX = 800.0` px (`backend/config.py`).
- Runtime adaptive default: When `focal_length_px` is not provided in the request or is $\le 0$, `DistanceEstimatorService` computes:
  $$f = \text{round}(W \times 0.9, 1)$$
  For standard $960 \times 600$ test images, $f = 960 \times 0.9 = 864.0$ px.
- Physical FOV correspondence:
  $$\text{FOV}_h = 2 \cdot \arctan\left(\frac{W}{2f}\right) = 2 \cdot \arctan(0.5555) \approx 58.1^\circ$$

#### Real-World Class Reference Heights ($H_{real}$)
Defined in `CLASS_REFERENCE_HEIGHTS` (`backend/services/distance_estimator.py`):

| Class Name | Prior Height ($H_{real}$, meters) | Reference Object Category |
|------------|-----------------------------------|---------------------------|
| `person` | 1.70 m | Standing adult human |
| `car` | 1.50 m | Standard passenger sedan/hatchback |
| `bicycle` | 1.00 m | Standard upright commuter bicycle |
| `motorcycle` | 1.10 m | Standard road motorcycle |
| `bus` | 3.20 m | Single-deck transit bus |
| `train` | 3.80 m | Standard railway passenger car |
| `truck` | 3.00 m | Medium/heavy commercial cargo truck |
| `traffic light` | 2.80 m | Post-mounted urban signal head |
| `chair` | 0.85 m | Standard dining/office chair |
| `bottle` | 0.25 m | Standard 500ml beverage bottle |
| `forklift`* | 2.20 m | Industrial warehouse forklift (*frontend geometry only) |
| *Fallback* | 1.50 m | `DEFAULT_REFERENCE_HEIGHT` (backend) |
| *Config Fallback* | 1.65 m | `DEFAULT_REAL_OBJECT_HEIGHT` (`backend/config.py`) |

---

### 2.3 Reference Scenes & Ground-Truth Verification

The repository specifies 3 reference scenes (1 synthetically generated in code, 2 mock/benchmark scenarios):

#### Reference Scene 1: Urban Traffic Roadway (`traffic_urban.jpg`)
Generated via `generate_sample_traffic_scene(output_path)` (`backend/utils/image_utils.py`):
- **Image Resolution**: $W = 960$ px, $H = 600$ px. Diagonal $= \sqrt{960^2 + 600^2} = 1132.08$ px.
- **Adaptive Focal Length**: $f = 960 \times 0.9 = 864.0$ px.
- **Principal Point**: $(c_{img\_x}, c_{img\_y}) = (480.0, 300.0)$ px.

**Ground-Truth Object A (Car 1 - Red Sedan)**:
- Bounding Box: `[140, 360, 400, 500]`
- Dimensions: Width $w_1 = 260$ px, Height $h_1 = 140$ px.
- Centroid: $(cx_1, cy_1) = (270.0, 430.0)$ px.
- Class: `car` ($H_{real} = 1.50$ m).
- Pinhole Depth:
  $$Z_1 = \frac{864.0 \cdot 1.50}{140} = 9.2571 \text{ m} \approx 9.26 \text{ m}$$
- 3D Coordinates:
  $$X_1 = \frac{(270 - 480) \cdot 9.2571}{864.0} = \frac{-210 \cdot 9.2571}{864.0} = -2.250 \text{ m}$$
  $$Y_1 = \frac{(430 - 300) \cdot 9.2571}{864.0} = \frac{130 \cdot 9.2571}{864.0} = +1.393 \text{ m}$$
  $$(X_1, Y_1, Z_1) = (-2.250\text{ m}, +1.393\text{ m}, +9.257\text{ m})$$

**Ground-Truth Object B (Car 2 - Cyan Sedan)**:
- Bounding Box: `[580, 310, 790, 420]`
- Dimensions: Width $w_2 = 210$ px, Height $h_2 = 110$ px.
- Centroid: $(cx_2, cy_2) = (685.0, 365.0)$ px.
- Class: `car` ($H_{real} = 1.50$ m).
- Pinhole Depth:
  $$Z_2 = \frac{864.0 \cdot 1.50}{110} = 11.7818 \text{ m} \approx 11.78 \text{ m}$$
- 3D Coordinates:
  $$X_2 = \frac{(685 - 480) \cdot 11.7818}{864.0} = \frac{205 \cdot 11.7818}{864.0} = +2.795 \text{ m}$$
  $$Y_2 = \frac{(365 - 300) \cdot 11.7818}{864.0} = \frac{65 \cdot 11.7818}{864.0} = +0.886 \text{ m}$$
  $$(X_2, Y_2, Z_2) = (+2.795\text{ m}, +0.886\text{ m}, +11.782\text{ m})$$

**Ground-Truth Relative Distance Calculation**:
- $\Delta X = 2.795 - (-2.250) = 5.045$ m
- $\Delta Y = 0.886 - 1.393 = -0.507$ m
- $\Delta Z = 11.782 - 9.257 = 2.525$ m
- Relative 3D Distance $D_{3D}$:
  $$D_{3D} = \sqrt{5.045^2 + (-0.507)^2 + 2.525^2} = \sqrt{25.452 + 0.257 + 6.376} = \sqrt{32.085} = 5.664 \text{ m} \approx 5.66 \text{ m}$$
- 2D Pixel Distance:
  $$\Delta x = 685 - 270 = 415 \text{ px}, \quad \Delta y = 365 - 430 = -65 \text{ px}$$
  $$D_{pixel} = \sqrt{415^2 + (-65)^2} = \sqrt{172225 + 4225} = \sqrt{176450} = 420.06 \text{ px} \approx 420.1 \text{ px}$$
- Normalized Distance:
  $$D_{norm\%} = \frac{420.06}{1132.08} \times 100\% = 37.105\% \approx 37.1\%$$

---

## 3. Authoritative Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | API Routing | Root Service Info (`GET /`) | Returns service name, domain, and list of available endpoints | None | JSON object with project name, domain, status, endpoint list | 500 on server crash | `backend/app.py:20` |
| 2 | API Routing | Health Check (`GET /api/health`) | Verifies backend liveness, model load status, model filename, load error | None | JSON object with `status`, `yolo_loaded`, `model_name`, `load_error` | Returns 200 with `yolo_loaded: false` if model init failed | `backend/routes/api.py:29` |
| 3 | API Detection | Multipart Image Ingestion | Ingests file uploads via multipart form data with file extension check | `image` (binary file), optional `conf`, `iou` | Full detection JSON with bboxes, confidence, base64 images | 400 on missing file, invalid extension, or unreadable bytes | `backend/routes/api.py:53` |
| 4 | API Detection | Base64 Image Ingestion | Ingests raw base64 or Data URL base64 encoded images via JSON body | `image_base64` (string), optional `filename`, `conf`, `iou` | Full detection JSON with bboxes, confidence, base64 images | 400 on decode failure; 500 on invalid base64 padding | `backend/routes/api.py:60` |
| 5 | Detection Engine | YOLOv8 Inference | Executes Ultralytics YOLO inference with confidence and IoU NMS filtering | OpenCV BGR image, `conf_threshold`, `iou_threshold` | Structured detections list with bboxes, class IDs, labels | 500 if unhandled model exception; falls back if model uninitialized | `backend/services/yolo_detector.py:27` |
| 6 | Detection Engine | Annotation Rendering | Renders multi-color bounding boxes, centroid dots, and label badges | Image array, detections list | Annotated OpenCV BGR image | Internal drawing; silent on empty detections | `backend/services/yolo_detector.py:110` |
| 7 | Detection Engine | Fallback Simulation Detections | Generates synthetic car and person detections if YOLO model fails to load | Image dimensions (width, height) | 2 synthetic detection objects | Never throws; always succeeds | `backend/services/yolo_detector.py:133` |
| 8 | Distance API | Object Spatial Distance (`POST /api/distance`) | Calculates 3D distance, 2D pixel separation, and returns annotated vector image | JSON with `object_a`, `object_b`, `image_dimensions`, optional `focal_length_px`, `image_base64` | Metrics JSON with $Z_1$, $Z_2$, $D_{3D}$, $D_{pixel}$, $D_{norm\%}$, visualization image | 400 if `object_a` or `object_b` missing; 500 if malformed json | `backend/routes/api.py:78` |
| 9 | Distance Engine | Multi-Format Centroid Extraction | Extracts $(cx, cy)$ from `center` array, `centroid` dict, or `bbox` array | Object dictionary | $(cx, cy)$ floating point coordinates | Defaults to $(0.0, 0.0)$ if neither exists | `backend/services/distance_estimator.py:35` |
| 10 | Distance Engine | Monocular Pinhole Depth Estimation | Computes depth $Z$ along optical axis using class prior height and focal length | $f$, $H_{real}$, $h_{pixels}$ | Depth $Z$ in meters | Clamps height to `max(1, h)` to prevent division by zero | `backend/services/distance_estimator.py:64` |
| 11 | Distance Engine | 3D Camera Coordinate Projection | Back-projects 2D image coordinates to 3D camera frame $(X, Y, Z)$ | Centroid $(cx, cy)$, Depth $Z$, Focal length $f$, Sensor dimensions $(W, H)$ | 3D coordinates in meters | Presumes principal point at $(W/2, H/2)$ | `backend/services/distance_estimator.py:71` |
| 12 | Distance Engine | Distance Overlay Rendering | Draws line between centroids, letter badges (A, B), and distance banner | Image base64, object_a, object_b, pixel distance, meter distance | Annotated Data URL (`data:image/jpeg;base64,...`) | Returns `null` on decode error without failing response | `backend/services/distance_estimator.py:113` |
| 13 | Synthetic Ground Truth | Traffic Scene Generator | Procedurally generates synthetic 960x600 roadway with 2 cars for calibration | Output file path | Saved image file path | Writes file directly via OpenCV | `backend/utils/image_utils.py:40` |
| 14 | Client Geometry | Frontend Fallback Distance Calculator | Implements identical monocular 3D distance math in JavaScript for offline mode | `objA`, `objB`, `imgWidth`, `imgHeight`, `focalLengthPx` | Client metrics object matching backend metrics schema | Returns `null` if objects missing | `frontend/src/utils/geometry.js:1` |

---

## 4. Edge Cases & Observed Fragilities

| # | Feature | Input / Condition | Observed / Code Behavior | Severity | Root Cause & Recommendation |
|---|---------|-------------------|--------------------------|----------|-----------------------------|
| 1 | `POST /api/detect` | Zero objects in image (e.g. blank canvas) | Returns 200 OK with `total_objects: 0`, `detections: []`, `classes_detected: []`. Frontend disables distance calculation. | Low / Normal | Expected behavior; benchmark suite must verify 200 OK and empty array. |
| 2 | `POST /api/detect` | Non-numeric `conf` or `iou` (e.g. `conf="abc"`) | Raises `ValueError` inside `float(...)`; caught by generic `except Exception` returning HTTP 500. | Medium | Should validate and return HTTP 400 Bad Request with descriptive message. |
| 3 | `POST /api/detect` | Corrupted image bytes (e.g. random text file renamed `.jpg`) | `cv2.imdecode` returns `None`; caught by `if cv_img is None:` returning HTTP 400: `Unable to decode provided image`. | Well-handled | Proper 400 response. |
| 4 | `POST /api/detect` | Missing file and missing `image_base64` | Returns HTTP 400: `No image provided. Upload a file or pass 'image_base64'.` | Well-handled | Proper 400 response. |
| 5 | `POST /api/detect` | Unsupported extension (e.g. `.gif`, `.bmp`, `.tiff`) | Returns HTTP 400: `Unsupported file extension '.xyz'. Allowed: jpg, jpeg, png, webp`. | Well-handled | Proper 400 response. |
| 6 | `POST /api/detect` | File size > 16 MB | Flask halts request with HTTP 413 Payload Too Large. | Well-handled | Governed by `Config.MAX_CONTENT_LENGTH`. |
| 7 | `POST /api/distance` | Missing `object_a` or `object_b` (e.g. `{}`) | Returns HTTP 400: `Both object_a and object_b are required`. | Well-handled | Proper 400 response. |
| 8 | `POST /api/distance` | Empty JSON request body or malformed JSON | `request.get_json(force=True)` raises `BadRequest` or returns `None`; accessing `data.get(...)` raises `AttributeError` returning HTTP 500. | High | Should wrap `get_json` safely and return HTTP 400 on malformed JSON. |
| 9 | `POST /api/distance` | Zero bounding box height (`height: 0`) | Guarded by `max(1, object.get("height", 100))`; prevents ZeroDivisionError; depth calculated using $h=1$. | Well-handled | Robust defense. |
| 10 | `POST /api/distance` | Non-existent class name (e.g. `"class_name": "alien"`) | Falls back to `DEFAULT_REFERENCE_HEIGHT = 1.50` meters; calculates distance successfully. | Well-handled | Predictable fallback behavior. |
| 11 | `POST /api/distance` | Extreme aspect ratios (e.g. $w=1, h=1000$ or $w=1000, h=1$) | Mathematical computation proceeds without overflow; depth scales inversely with height. | Normal | Numerically stable. |
| 12 | `POST /api/distance` | Missing or zero focal length (`focal_length_px: 0` or omitted) | Automatically calculates $f = \text{round}(W \times 0.9, 1)$. | Well-handled | Self-calibrating default. |
| 13 | `POST /api/distance` | Missing image dimensions (`image_dimensions: null`) | Defaults to `{"width": 1000, "height": 800}` in service layer, or `{"width": 800, "height": 600}` in route. | Minor discrepancy | Route uses default $(800, 600)$, service uses default $(1000, 800)$. Recommend unifying. |
| 14 | `POST /api/distance` | Invalid Base64 in `image_base64` | `_draw_distance_measurement` catches exception, prints log, and returns `visualization_image: null`; main response returns 200 OK with metrics. | Well-handled | Non-blocking visualization failure. |

---

## 5. Architectural & Implementation Insights for Subsequent Phases

1. **Benchmark Suite Requirements (R1)**:
   - Ground truth distance tolerances: For the calibrated `traffic_urban.jpg` reference scene, Object A (`car`) and Object B (`car`) have mathematically exact reference depth $Z_1 = 9.26$ m, $Z_2 = 11.78$ m, and relative 3D separation $D_{3D} = 5.66$ m. The benchmark suite must assert that calculated distances match these bounded tolerances within $\pm 0.05$ m.
   - Output format must be written to `benchmark_results.json` containing precision, recall, mean inference time (ms), and relative distance estimation error.
2. **Stress & Concurrency Pipeline (R2)**:
   - Both `/api/detect` and `/api/distance` must be tested under 50+ concurrent virtual clients.
   - Since CPU inference for YOLOv8 forward pass takes $\approx 15\text{--}40$ ms per frame, 50 concurrent requests in standard synchronous Flask/Werkzeug dev server will queue and fail the $<80$ ms P95 budget unless asynchronous concurrency or multi-worker WSGI/threading is handled.
3. **Integration & Edge Case Suite (R3)**:
   - Must write pytest test cases covering all 4 supported MIME formats (`image/jpeg`, `image/png`, `image/webp`, and Base64 data URLs).
   - Must write tests covering all 14 edge cases listed in Section 4.
4. **Containerization Setup (R4)**:
   - Must use `opencv-python-headless` or install Linux `libgl1` and `libglib2.0-0` packages in Dockerfile to prevent OpenCV runtime import errors.
   - Must mount/cache `yolov8n.pt` to avoid re-downloading PyTorch model weights on container spin-up.
