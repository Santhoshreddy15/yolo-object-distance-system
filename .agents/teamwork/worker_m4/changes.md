# Changes Summary — Milestone 4 (Containerized Production Deployment)

**Worker**: `worker_m4`  
**Milestone**: M4 (R4 Containerized Production Deployment)  
**Date**: 2026-11-01  

---

## 1. Files Created

### 1. `backend/Dockerfile`
- **Base image**: `python:3.11-slim` for minimal container footprint.
- **System dependencies**: Installed `curl`, `libgl1`, and `libglib2.0-0` (required for headless OpenCV image operations), followed by `apt-get clean` and `/var/lib/apt/lists/*` cache deletion.
- **Python dependencies**: Copies `/app/requirements.txt` and executes `pip install --no-cache-dir -r /app/requirements.txt`.
- **Model weights caching**: Baked `yolov8n.pt` (6.5MB) directly into `/app/yolov8n.pt`, backed by environment variable `YOLO_MODEL=/app/yolov8n.pt` and `YOLO_WEIGHTS_PATH=/app/yolov8n.pt`. This ensures Ultralytics never attempts to download weights from external repositories on container startup or restart.
- **Application source**: Copies `backend/` into `/app/backend/` and ensures `/app/backend/uploads` and `/app/backend/sample_images` exist.
- **WSGI Runner**: Configured production Gunicorn WSGI server:
  ```bash
  gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 backend.app:create_app()
  ```
  Provides multi-worker, multi-threaded request processing to handle concurrent clients without connection dropping.
- **Healthcheck probe**: Configured automated healthcheck probe:
  ```dockerfile
  HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
      CMD curl -f http://localhost:5000/api/health || exit 1
  ```

### 2. `frontend/nginx.conf`
- **Reverse proxy**: Forwards all `/api/` traffic directly to `http://backend:5000/api/` with HTTP/1.1 upgrade headers, real IP forwarding, and generous 60s/120s timeouts for deep learning inference workloads.
- **SPA Routing**: Implements `try_files $uri $uri/ /index.html;` ensuring client-side routes in React Router / Vite do not return HTTP 404.
- **Asset caching**: Configures `Cache-Control "public, max-age=31536000, immutable"` and 1-year expiry for static JS, CSS, images, and fonts.
- **Gzip compression**: Enables compression for json, html, css, js, xml, and svg assets.
- **Payload limits**: Sets `client_max_body_size 25M;` to support large photographic image uploads up to 16MB.
- **Healthcheck endpoint**: Exposes `/health` returning HTTP 200 with `text/plain` body `"healthy\n"`.

### 3. `frontend/Dockerfile`
- **Multi-stage architecture**:
  - **Stage 1 (`builder`)**: Uses `node:20-alpine`, runs `npm ci || npm install`, injects build argument `ARG VITE_API_URL=/api`, and compiles the frontend bundle via `npm run build`.
  - **Stage 2 (`runner`)**: Uses `nginx:alpine` for minimal attack surface and minimal image size. Copies static build from builder stage to `/usr/share/nginx/html`, copies custom `nginx.conf`, installs `curl` for container health checks, and configures automated healthcheck probe on `http://localhost:80/health`.

### 4. `docker-compose.yml`
- **Multi-service orchestration**: Defines `backend` (port 5000) and `frontend` (port 3000 mapped to internal port 80).
- **Healthcheck dependency**: `frontend` declares `depends_on: backend: condition: service_healthy`, guaranteeing that the web UI is not exposed until the computer vision model has been loaded and initialized into memory.
- **Volume caching**: Configures `model-cache` persistent volume, `./yolov8n.pt:/app/yolov8n.pt:ro` read-only mount, and `backend-uploads` volume.
- **Network isolation**: Dedicated `yolo-network` bridge network for inter-container communication.
- **Graceful shutdown**: Configures `stop_grace_period` (10s for backend, 5s for frontend) allowing in-flight inference requests to complete before termination.

### 5. `.dockerignore` & `frontend/.dockerignore`
- Excludes `.git`, `.agents/`, `__pycache__`, virtual environments, test caches, node_modules, and build outputs.
- Explicitly whitelists `!yolov8n.pt`, `!backend/`, and `!requirements.txt` to guarantee clean, deterministic builds.

### 6. `.agents/teamwork/worker_m4/verify_docker_setup.py`
- Automated static validation tool verifying all syntax, directives, dependencies, and configuration consistency rules across the 5 Docker deployment artifacts.
