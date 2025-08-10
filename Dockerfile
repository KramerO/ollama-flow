# Ollama Flow - Multi-Stage Docker Build
# Optimized for running AI agents in containerized environment

# Stage 1: Build stage with development dependencies
FROM python:3.11-slim-bullseye AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage with minimal dependencies
FROM python:3.11-slim-bullseye AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    OLLAMA_HOST=host.docker.internal:11434

# Create non-root user for security
RUN groupadd -r ollama && useradd -r -g ollama -d /app -s /bin/bash ollama

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/ollama/.local

# Copy application code
COPY --chown=ollama:ollama . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/tmp && \
    chown -R ollama:ollama /app

# Create health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:8080/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Switch to non-root user
USER ollama

# Make PATH available for installed packages
ENV PATH="/home/ollama/.local/bin:$PATH"

# Expose port for dashboard
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Default command
CMD ["python3", "enhanced_framework.py", "--docker-mode"]