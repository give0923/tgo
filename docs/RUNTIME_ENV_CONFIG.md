# Runtime Environment Configuration for Frontend Services

## Overview

The frontend services (`tgo-web` and `tgo-widget-app`) now support **runtime environment configuration** through Docker environment variables. This allows you to build a single Docker image and deploy it to different environments without rebuilding.

## Key Features

✅ **Build Once, Deploy Anywhere**: Build the image once, use it in dev/test/prod  
✅ **Dynamic Configuration**: Change API endpoints without rebuilding  
✅ **Backward Compatible**: Falls back to build-time env vars if runtime vars not provided  
✅ **Zero Downtime**: Update configuration by restarting containers  

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Docker Container Startup                                    │
├─────────────────────────────────────────────────────────────┤
│ 1. docker-entrypoint.sh runs                                │
│    ├─ Reads environment variables (API_BASE_URL, etc.)     │
│    └─ Generates /usr/share/nginx/html/env-config.js        │
│                                                              │
│ 2. Nginx starts                                              │
│    └─ Serves static files + env-config.js                  │
│                                                              │
│ 3. Browser loads index.html                                 │
│    ├─ Loads <script src="/env-config.js"></script>         │
│    └─ window.ENV is now available                          │
│                                                              │
│ 4. React app initializes                                    │
│    └─ Reads config from window.ENV (runtime)               │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Priority

The frontend code uses this priority order to determine configuration:

1. **Runtime** (highest): `window.ENV.VITE_API_BASE_URL` (from env-config.js)
2. **Build-time**: `import.meta.env.VITE_API_BASE_URL` (from Vite build)
3. **Default** (lowest): `http://localhost:8000`

## Environment Variables

### tgo-web

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Backend API base URL |
| `WUKONGIM_WS_URL` | `ws://localhost:5200` | WuKongIM WebSocket URL |
| `DEBUG_MODE` | `false` | Enable debug logging |

### tgo-widget-app

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Backend API base URL |

## Usage Examples

### Docker Run

```bash
# Run with custom API endpoint
docker run -e API_BASE_URL=http://api.example.com:8000 \
           -p 3000:80 \
           ghcr.io/tgoai/tgo/tgo-web:latest

# Run with custom WebSocket URL
docker run -e API_BASE_URL=http://api.example.com:8000 \
           -e WUKONGIM_WS_URL=wss://im.example.com:5200 \
           -p 3000:80 \
           ghcr.io/tgoai/tgo/tgo-web:latest
```

### Docker Compose

```yaml
services:
  tgo-web:
    image: ghcr.io/tgoai/tgo/tgo-web:latest
    environment:
      API_BASE_URL: http://api.example.com:8000
      WUKONGIM_WS_URL: wss://im.example.com:5200
      DEBUG_MODE: "true"
    ports:
      - "3000:80"

  tgo-widget-app:
    image: ghcr.io/tgoai/tgo/tgo-widget-app:latest
    environment:
      API_BASE_URL: http://api.example.com:8000
    ports:
      - "3001:80"
```

### Using .env File

```bash
# .env
API_BASE_URL=http://api.staging.example.com:8000
WUKONGIM_WS_URL=wss://im.staging.example.com:5200

# Run with env file
docker run --env-file .env -p 3000:80 ghcr.io/tgoai/tgo/tgo-web:latest
```

## Implementation Details

### Files Modified

**tgo-web**:
- `Dockerfile` - Added entrypoint script
- `docker-entrypoint.sh` - New script to generate runtime config
- `index.html` - Added `<script src="/env-config.js"></script>`
- `src/services/api.ts` - Updated to read from `window.ENV`
- `src/utils/url.ts` - Updated to read from `window.ENV`

**tgo-widget-app**:
- `Dockerfile` - Added entrypoint script
- `docker-entrypoint.sh` - New script to generate runtime config
- `index.html` - Added `<script src="/env-config.js"></script>`
- `src/App.tsx` - Updated to read from `window.ENV`

**Compose Files**:
- `docker-compose.yml` - Added environment variables
- `docker-compose.source.yml` - Added environment variables

### Generated Configuration File

At runtime, `docker-entrypoint.sh` generates `/usr/share/nginx/html/env-config.js`:

```javascript
// Runtime environment configuration for tgo-web
// Generated at container startup from environment variables
window.ENV = {
  VITE_API_BASE_URL: 'http://api.example.com:8000',
  VITE_WUKONGIM_WS_URL: 'wss://im.example.com:5200',
  VITE_DEBUG_MODE: true,
};
```

## Migration Guide

### For Existing Deployments

If you're currently using build-time environment variables:

**Before** (build-time):
```bash
docker build --build-arg VITE_API_BASE_URL=http://api.example.com:8000 \
             -t tgo-web:latest .
docker run -p 3000:80 tgo-web:latest
```

**After** (runtime):
```bash
# Build once (no build args needed)
docker build -t tgo-web:latest .

# Run with environment variables
docker run -e API_BASE_URL=http://api.example.com:8000 \
           -p 3000:80 tgo-web:latest
```

### Backward Compatibility

The implementation is fully backward compatible:

1. If you provide runtime env vars → they are used
2. If you don't provide runtime env vars but have build-time vars → build-time vars are used
3. If neither are provided → defaults are used

## Troubleshooting

### Configuration Not Applied

**Problem**: Changes to environment variables don't take effect

**Solution**: 
1. Restart the container: `docker restart tgo-web`
2. Verify env vars are set: `docker inspect tgo-web | grep -A 20 Env`
3. Check generated config: `docker exec tgo-web cat /usr/share/nginx/html/env-config.js`

### API Requests Failing

**Problem**: Frontend can't reach the API

**Solution**:
1. Verify API_BASE_URL is correct: `docker logs tgo-web | grep "API_BASE_URL"`
2. Test connectivity: `docker exec tgo-web curl http://api.example.com:8000/health`
3. Check browser console for errors

### WebSocket Connection Issues

**Problem**: Real-time features not working

**Solution**:
1. Verify WUKONGIM_WS_URL is correct
2. Ensure WebSocket protocol (ws:// or wss://) matches your setup
3. Check firewall/proxy allows WebSocket connections

## Best Practices

1. **Use HTTPS in Production**
   ```bash
   API_BASE_URL=https://api.example.com:8000
   WUKONGIM_WS_URL=wss://im.example.com:5200
   ```

2. **Use Environment-Specific Compose Files**
   ```bash
   docker-compose -f docker-compose.yml \
                  -f docker-compose.prod.yml up -d
   ```

3. **Document Your Configuration**
   ```bash
   # Create .env.example
   API_BASE_URL=https://api.example.com:8000
   WUKONGIM_WS_URL=wss://im.example.com:5200
   DEBUG_MODE=false
   ```

4. **Use Secrets for Sensitive Data**
   ```bash
   docker run --secret api_key \
              -e API_BASE_URL=https://api.example.com:8000 \
              tgo-web:latest
   ```

## Technical Details

### How the Entrypoint Script Works

The `docker-entrypoint.sh` script:

1. **Reads environment variables** from the container's environment
2. **Generates JavaScript configuration** with those values
3. **Writes to `/usr/share/nginx/html/env-config.js`**
4. **Starts Nginx** to serve the application

```bash
#!/bin/sh
set -e

CONFIG_FILE="/usr/share/nginx/html/env-config.js"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

cat > "$CONFIG_FILE" << EOF
window.ENV = {
  VITE_API_BASE_URL: '$API_BASE_URL',
};
EOF

exec nginx -g "daemon off;"
```

### How Frontend Code Reads Configuration

The frontend code checks multiple sources in priority order:

```typescript
// Priority: runtime > build-time > default
const getApiBaseUrl = (): string => {
  // 1. Check runtime config (window.ENV)
  if (typeof window !== 'undefined' && (window as any).ENV?.VITE_API_BASE_URL) {
    return (window as any).ENV.VITE_API_BASE_URL;
  }
  // 2. Check build-time env var
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // 3. Use default
  return 'http://localhost:8000';
};
```

## Related Documentation

- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Nginx Configuration](https://nginx.org/en/docs/)

