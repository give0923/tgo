# Frontend Runtime Configuration - Quick Start

## TL;DR

Frontend services now support **runtime environment configuration**. Build once, deploy anywhere!

## Quick Examples

### Local Development

```bash
# Using docker-compose (default localhost)
./tgo.sh install
./tgo.sh start

# Or with custom API endpoint
API_BASE_URL=http://api.dev.local:8000 docker-compose up -d tgo-web
```

### Staging Environment

```bash
# Using environment variables
docker run -e API_BASE_URL=https://api.staging.example.com:8000 \
           -e WUKONGIM_WS_URL=wss://im.staging.example.com:5200 \
           -p 3000:80 \
           ghcr.io/tgoai/tgo/tgo-web:latest
```

### Production Environment

```bash
# Using .env file
cat > .env.prod << EOF
API_BASE_URL=https://api.example.com:8000
WUKONGIM_WS_URL=wss://im.example.com:5200
DEBUG_MODE=false
EOF

docker-compose --env-file .env.prod up -d
```

## Environment Variables

### tgo-web

```bash
API_BASE_URL=http://api.example.com:8000      # Backend API
WUKONGIM_WS_URL=ws://im.example.com:5200      # WebSocket (ws:// or wss://)
DEBUG_MODE=false                               # Enable debug logging
```

### tgo-widget-app

```bash
API_BASE_URL=http://api.example.com:8000      # Backend API
```

## How It Works

1. **Build**: `docker build -t tgo-web:latest .` (no build args needed!)
2. **Run**: `docker run -e API_BASE_URL=... tgo-web:latest`
3. **Entrypoint**: Script generates `/env-config.js` with your settings
4. **Frontend**: Reads config from `window.ENV` at runtime

## Verify Configuration

```bash
# Check what config was generated
docker exec tgo-web cat /usr/share/nginx/html/env-config.js

# Should output something like:
# window.ENV = {
#   VITE_API_BASE_URL: 'http://api.example.com:8000',
#   VITE_WUKONGIM_WS_URL: 'wss://im.example.com:5200',
#   VITE_DEBUG_MODE: false,
# };
```

## Common Scenarios

### Scenario 1: Change API Endpoint Without Rebuilding

```bash
# Old way (rebuild required)
docker build --build-arg VITE_API_BASE_URL=http://new-api:8000 -t tgo-web .

# New way (just restart)
docker stop tgo-web
docker run -e API_BASE_URL=http://new-api:8000 -p 3000:80 tgo-web:latest
```

### Scenario 2: Use HTTPS in Production

```bash
docker run -e API_BASE_URL=https://api.example.com:8000 \
           -e WUKONGIM_WS_URL=wss://im.example.com:5200 \
           -p 3000:80 \
           tgo-web:latest
```

### Scenario 3: Docker Compose with Multiple Environments

```yaml
# docker-compose.yml
services:
  tgo-web:
    image: tgo-web:latest
    environment:
      API_BASE_URL: ${API_BASE_URL:-http://localhost:8000}
      WUKONGIM_WS_URL: ${WUKONGIM_WS_URL:-ws://localhost:5200}
    ports:
      - "3000:80"
```

```bash
# Run with different configs
API_BASE_URL=http://dev-api:8000 docker-compose up -d
API_BASE_URL=https://staging-api:8000 docker-compose up -d
API_BASE_URL=https://prod-api:8000 docker-compose up -d
```

## Backward Compatibility

✅ Still works with build-time environment variables:

```bash
# Old way still works
docker build --build-arg VITE_API_BASE_URL=http://api:8000 -t tgo-web .
docker run -p 3000:80 tgo-web:latest
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Config not applied | Restart container: `docker restart tgo-web` |
| API requests failing | Check: `docker logs tgo-web \| grep API_BASE_URL` |
| WebSocket not working | Verify protocol (ws:// vs wss://) matches your setup |

## Files Changed

- `repos/tgo-web/Dockerfile` - Added entrypoint
- `repos/tgo-web/docker-entrypoint.sh` - New
- `repos/tgo-web/index.html` - Added script tag
- `repos/tgo-web/src/services/api.ts` - Updated config reading
- `repos/tgo-web/src/utils/url.ts` - Updated config reading
- `repos/tgo-widget-app/Dockerfile` - Added entrypoint
- `repos/tgo-widget-app/docker-entrypoint.sh` - New
- `repos/tgo-widget-app/index.html` - Added script tag
- `repos/tgo-widget-app/src/App.tsx` - Updated config reading
- `docker-compose.yml` - Added environment variables
- `docker-compose.source.yml` - Added environment variables

## Next Steps

1. Rebuild images: `./tgo.sh build --source all`
2. Test with custom API: `API_BASE_URL=http://custom-api:8000 docker-compose up -d`
3. Verify config: `docker exec tgo-web cat /usr/share/nginx/html/env-config.js`

## Full Documentation

See `docs/RUNTIME_ENV_CONFIG.md` for detailed information.

