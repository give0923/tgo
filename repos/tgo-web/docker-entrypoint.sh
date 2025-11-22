#!/bin/sh
# Docker entrypoint script for tgo-web
# Generates runtime configuration from environment variables

set -e

# Configuration file path
CONFIG_FILE="/usr/share/nginx/html/env-config.js"

# Get environment variables with defaults
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
DEBUG_MODE="${DEBUG_MODE:-false}"

# Generate env-config.js with runtime configuration
cat > "$CONFIG_FILE" << EOF
// Runtime environment configuration for tgo-web
// Generated at container startup from environment variables
window.ENV = {
  VITE_API_BASE_URL: '$API_BASE_URL',
  VITE_DEBUG_MODE: $DEBUG_MODE,
};
EOF

echo "[INFO] Generated runtime configuration:"
echo "[INFO]   API_BASE_URL: $API_BASE_URL"
echo "[INFO]   DEBUG_MODE: $DEBUG_MODE"

# Start Nginx
exec nginx -g "daemon off;"

