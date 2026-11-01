#!/usr/bin/env python3
"""
Static Verification Script for YOLO Object Distance System Docker Deployment Configuration
Validates syntax, structure, parameters, and consistency of:
- backend/Dockerfile
- frontend/Dockerfile
- frontend/nginx.conf
- docker-compose.yml
- .dockerignore
"""

import sys
from pathlib import Path
import re

def validate_yaml_file(compose_path: Path) -> dict:
    content = compose_path.read_text(encoding="utf-8")
    errors = []
    
    # Check top-level keys
    if "services:" not in content:
        errors.append("Missing 'services:' block in docker-compose.yml")
    if "backend:" not in content:
        errors.append("Missing 'backend' service in docker-compose.yml")
    if "frontend:" not in content:
        errors.append("Missing 'frontend' service in docker-compose.yml")
        
    # Check healthcheck dependency
    if "condition: service_healthy" not in content:
        errors.append("Missing 'condition: service_healthy' dependency in docker-compose.yml")
        
    # Check port mappings
    if "5000:5000" not in content:
        errors.append("Missing port mapping '5000:5000' for backend")
    if "3000:80" not in content:
        errors.append("Missing port mapping '3000:80' for frontend")
        
    # Check model volume caching
    if "model-cache" not in content:
        errors.append("Missing 'model-cache' volume definition")
    if "yolov8n.pt" not in content:
        errors.append("Missing 'yolov8n.pt' volume mount")
        
    # Check network
    if "networks:" not in content:
        errors.append("Missing 'networks:' definition in docker-compose.yml")
        
    return {"file": str(compose_path), "valid": len(errors) == 0, "errors": errors}

def validate_backend_dockerfile(dockerfile_path: Path) -> dict:
    content = dockerfile_path.read_text(encoding="utf-8")
    errors = []
    
    if "FROM python:3.11-slim" not in content:
        errors.append("Backend Dockerfile does not use python:3.11-slim as base image")
    if "libgl1" not in content or "libglib2.0-0" not in content:
        errors.append("Backend Dockerfile missing OpenCV headless system libraries (libgl1, libglib2.0-0)")
    if "curl" not in content:
        errors.append("Backend Dockerfile missing curl for healthcheck")
    if "requirements.txt" not in content:
        errors.append("Backend Dockerfile does not install requirements.txt")
    if "yolov8n.pt" not in content:
        errors.append("Backend Dockerfile does not bake in yolov8n.pt model caching")
    if "gunicorn" not in content:
        errors.append("Backend Dockerfile does not run via Gunicorn WSGI server")
    if "HEALTHCHECK" not in content or "/api/health" not in content:
        errors.append("Backend Dockerfile missing automated healthcheck on /api/health")
    if "EXPOSE 5000" not in content:
        errors.append("Backend Dockerfile missing EXPOSE 5000")
        
    return {"file": str(dockerfile_path), "valid": len(errors) == 0, "errors": errors}

def validate_frontend_dockerfile(dockerfile_path: Path) -> dict:
    content = dockerfile_path.read_text(encoding="utf-8")
    errors = []
    
    if "FROM node:20-alpine AS builder" not in content:
        errors.append("Frontend Dockerfile missing Stage 1 'node:20-alpine AS builder'")
    if "FROM nginx:alpine AS runner" not in content:
        errors.append("Frontend Dockerfile missing Stage 2 'nginx:alpine AS runner'")
    if "COPY --from=builder" not in content or "/usr/share/nginx/html" not in content:
        errors.append("Frontend Dockerfile does not copy static assets from builder stage")
    if "nginx.conf" not in content:
        errors.append("Frontend Dockerfile does not copy custom nginx.conf")
    if "apk --no-cache add curl" not in content:
        errors.append("Frontend Dockerfile missing curl install in alpine")
    if "HEALTHCHECK" not in content or "/health" not in content:
        errors.append("Frontend Dockerfile missing automated healthcheck probe")
    if "EXPOSE 80" not in content:
        errors.append("Frontend Dockerfile missing EXPOSE 80")
        
    return {"file": str(dockerfile_path), "valid": len(errors) == 0, "errors": errors}

def validate_nginx_conf(nginx_path: Path) -> dict:
    content = nginx_path.read_text(encoding="utf-8")
    errors = []
    
    # Check balanced braces
    open_braces = content.count("{")
    close_braces = content.count("}")
    if open_braces != close_braces:
        errors.append(f"Mismatched braces in nginx.conf (open: {open_braces}, close: {close_braces})")
        
    if "listen 80;" not in content:
        errors.append("nginx.conf does not listen on port 80")
    if "location /api/" not in content or "proxy_pass http://backend:5000/api/;" not in content:
        errors.append("nginx.conf does not reverse-proxy /api/ to http://backend:5000/api/")
    if "location /health" not in content:
        errors.append("nginx.conf missing /health healthcheck endpoint")
    if "try_files $uri $uri/ /index.html;" not in content:
        errors.append("nginx.conf missing SPA client routing fallback try_files")
    if "client_max_body_size" not in content:
        errors.append("nginx.conf missing client_max_body_size for large image uploads")
        
    return {"file": str(nginx_path), "valid": len(errors) == 0, "errors": errors}

def validate_dockerignore(ignore_path: Path) -> dict:
    content = ignore_path.read_text(encoding="utf-8")
    errors = []
    
    if ".git" not in content:
        errors.append(".dockerignore missing .git entry")
    if "node_modules" not in content:
        errors.append(".dockerignore missing node_modules entry")
    if "!yolov8n.pt" not in content:
        errors.append(".dockerignore does not whitelist !yolov8n.pt")
    if "!requirements.txt" not in content:
        errors.append(".dockerignore does not whitelist !requirements.txt")
        
    return {"file": str(ignore_path), "valid": len(errors) == 0, "errors": errors}

def run_all_validations(project_root: Path):
    results = [
        validate_backend_dockerfile(project_root / "backend" / "Dockerfile"),
        validate_frontend_dockerfile(project_root / "frontend" / "Dockerfile"),
        validate_nginx_conf(project_root / "frontend" / "nginx.conf"),
        validate_yaml_file(project_root / "docker-compose.yml"),
        validate_dockerignore(project_root / ".dockerignore")
    ]
    
    all_passed = True
    print("=" * 70)
    print("DOCKER INFRASTRUCTURE STATIC VERIFICATION REPORT")
    print("=" * 70)
    for res in results:
        status = "PASSED" if res["valid"] else "FAILED"
        print(f"[{status}] {res['file']}")
        if not res["valid"]:
            all_passed = False
            for err in res["errors"]:
                print(f"   - Error: {err}")
    print("=" * 70)
    if all_passed:
        print("All 5 Docker configuration files passed 100% of validation rules!")
    else:
        print("Validation failures detected!")
    print("=" * 70)
    return all_passed

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent.parent.parent
    success = run_all_validations(root)
    sys.exit(0 if success else 1)
