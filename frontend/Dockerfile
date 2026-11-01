# =============================================================================
# YOLO Object Detection & Distance Measurement System — Frontend Container
# Multi-stage production build: Node 20 builder -> Nginx Alpine runner
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Vite React application
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Clean installation of dependencies
RUN npm ci || npm install

# Copy application source code and configuration files
COPY . .

# Set API URL build argument and environment variable for production build
# Setting VITE_API_URL to /api enables same-origin relative requests routed by Nginx
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

# Compile production-optimized static assets into /app/dist
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production Nginx runtime
# -----------------------------------------------------------------------------
FROM nginx:alpine AS runner

# Labels for container metadata
LABEL maintainer="YOLO Object Distance System Team"
LABEL description="Production Nginx container serving React SPA with API reverse proxy"
LABEL version="1.0.0"

# Remove default static pages
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Install curl in alpine for automated container healthcheck probe
RUN apk --no-cache add curl

# Expose HTTP port
EXPOSE 80

# Automated container healthcheck against /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Launch Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
