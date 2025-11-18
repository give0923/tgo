# 🔧 Development Guide

## Quick Start

The TGO-Tech API includes automatic development data initialization for immediate testing and debugging.

### 🚀 Starting the API

```bash
# Start development server
make dev

# Or manually
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 🎯 Development Credentials

When running in development mode (`ENVIRONMENT=development`), the following test data is automatically created:

| Resource | Value | Description |
|----------|-------|-------------|
| **Project** | "Development Project" | Default test project |
| **API Key** | `dev` | For API authentication |
| **Username** | `dev` | Test staff account |
| **Password** | `dev` | Test staff password |

### 📚 API Documentation

- **Interactive Docs**: http://localhost:8000/v1/docs
- **ReDoc**: http://localhost:8000/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/v1/openapi.json
- **Health Check**: http://localhost:8000/health

### 🔐 Authentication Examples

#### Staff Login (JWT)
```bash
curl -X POST "http://localhost:8000/v1/staff/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dev&password=dev"
```

#### Using JWT Token
```bash
TOKEN="your_jwt_token_here"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/projects
```

#### Using API Key (for specific endpoints)
```bash
curl -H "X-API-Key: dev" \
  http://localhost:8000/v1/some-endpoint
```

## 🔒 Production Security

### Automatic Protection

- **Dev API Key Blocked**: The `dev` API key is automatically blocked in production
- **Environment Validation**: Development features only work when `ENVIRONMENT=development`
- **Security Alerts**: Attempts to use dev credentials in production are logged as security alerts

### Environment Configuration

```bash
# Development (default)
ENVIRONMENT=development

# Production
ENVIRONMENT=production
```

## 🛠️ Development Features

### Automatic Data Seeding

- **Idempotent**: Safe to run multiple times - won't create duplicates
- **Smart Detection**: Checks if development data already exists
- **Clean Logging**: Beautiful startup output with clear instructions

### Database Management

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Reset database (development only)
make db-reset
```

### Testing

```bash
# Run tests
make test

# Run with coverage
make test-coverage

# Lint code
make lint
```

## 🎨 Startup Output

The application displays a beautiful startup banner with:
- Application name and version
- Environment mode
- Database connection status
- Development credentials (in dev mode)
- Server endpoints and documentation links

Example development startup:
```
╔══════════════════════════════════════════════════════════════╗
║                    🚀 TGO-Tech API Service                   ║
║                  Core Business Logic Service                 ║
╚══════════════════════════════════════════════════════════════╝

📦 Version: 0.1.0
🌍 Environment: DEVELOPMENT

⚠️  DEVELOPMENT MODE ACTIVE
   • Development credentials enabled
   • DO NOT use in production!

🗄️  Connecting to database...
✅ Database connected
🔧 Initializing development data...
✅ Development data ready!

🎯 Quick Start Guide:
   📋 API Key: 'dev'
   👤 Login: 'dev' / 'dev'
   📖 Docs: http://localhost:8000/v1/docs

🌐 Server starting...
   📍 Listening on: http://0.0.0.0:8000
   📚 API Docs: http://localhost:8000/v1/docs
   🏥 Health Check: http://localhost:8000/health

🎉 TGO-Tech API Service is ready!
════════════════════════════════════════════════════════════════
```
