# TGO Web (React + Vite) - build and serve via Nginx

# --- Build stage ---
FROM node:20-alpine AS builder
WORKDIR /app
ENV CI=true

# Accept Vite build-time envs as build args and expose them to build
ARG VITE_WIDGET_PREVIEW_URL
ENV VITE_WIDGET_PREVIEW_URL=${VITE_WIDGET_PREVIEW_URL}

# Install deps
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Build
COPY . .
RUN yarn build

# --- Runtime stage ---
FROM nginx:alpine

# Optional: healthcheck dependency
RUN apk add --no-cache curl

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Simple SPA nginx config (fallback to index.html)
RUN printf 'server {\n  listen 80;\n  server_name _;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / {\n    try_files $uri $uri/ /index.html;\n  }\n}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost/ || exit 1

