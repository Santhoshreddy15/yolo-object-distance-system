# syntax=docker/dockerfile:1
# =============================================================================
# YOLO Object Detection & Distance Measurement System — Backend Container
# Production-ready Python 3.11 runtime with OpenCV headless & baked-in YOLOv8n
# =============================================================================

FROM python:3.11-slim

# Labels for container metadata
LABEL maintainer="YOLO Object Distance System Team"
LABEL description="Production Flask backend with Ultralytics YOLOv8n & Gunicorn WSGI"
LABEL version="1.0.0"

# Set environment variables for non-interactive installs and unbuffered Python output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=5000 \
    YOLO_MODEL=/app/yolov8n.pt \
    YOLO_WEIGHTS_PATH=/app/yolov8n.pt \
    FLASK_ENV=production

WORKDIR /app

# Install system dependencies required for OpenCV headless and curl for container healthcheck
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from build context and install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Bake-in cached YOLOv8 nano model weights to guarantee zero online downloads
COPY yolov8n.pt /app/yolov8n.pt

# Copy backend application source code
COPY backend/ /app/backend/

# Create runtime directories for image uploads and sample images
RUN mkdir -p /app/backend/uploads /app/backend/sample_images

# Expose backend REST API port
EXPOSE 5000

# Automated container healthcheck against Flask /api/health
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Launch production WSGI runner via Gunicorn with 4 worker processes and 2 threads per worker
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "backend.app:create_app()"]
