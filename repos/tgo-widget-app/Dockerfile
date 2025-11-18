# TGO Widget App (Vite) - build and serve via Nginx

# --- Build stage ---
FROM node:20-alpine AS builder
WORKDIR /app
ENV CI=true

# Build-time envs for Vite (must be defined BEFORE build)
ARG VITE_API_BASE
ENV VITE_API_BASE=${VITE_API_BASE}

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN echo "Building with VITE_API_BASE=${VITE_API_BASE}" && yarn build

# --- Runtime stage ---
FROM nginx:alpine
RUN apk add --no-cache curl

COPY --from=builder /app/dist /usr/share/nginx/html

# Simple static serving config
RUN printf 'server {\n  listen 80;\n  server_name _;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / {\n    try_files $uri $uri/ /index.html;\n  }\n}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost/ || exit 1

