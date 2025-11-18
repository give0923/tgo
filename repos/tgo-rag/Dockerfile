# Multi-stage Dockerfile for RAG Service

# Base stage with Python and system dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml ./
COPY poetry.lock* ./

# Development stage
FROM base AS development

# Install dependencies including dev dependencies
RUN poetry install --with dev --no-root && rm -rf $POETRY_CACHE_DIR

# Create uploads directory
RUN mkdir -p /app/uploads

# Copy source code
COPY . .

# Expose port
EXPOSE 8082

# Default command for development
CMD ["poetry", "run", "uvicorn", "src.rag_service.main:app", "--host", "0.0.0.0", "--port", "8082", "--reload"]

# Production stage
FROM base AS production

# Install only production dependencies
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Create non-root user
RUN groupadd -r rag && useradd -r -g rag rag

# Set home and cache directories for non-root user and ensure writable
ENV HOME=/home/rag XDG_CACHE_HOME=/home/rag/.cache
RUN mkdir -p /home/rag/.cache && chown -R rag:rag /home/rag

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs && \
    chown -R rag:rag /app

# Copy source code
COPY --chown=rag:rag . .

# Switch to non-root user
USER rag

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Default command for production
CMD ["poetry", "run", "uvicorn", "src.rag_service.main:app", "--host", "0.0.0.0", "--port", "8082", "--workers", "4"]
