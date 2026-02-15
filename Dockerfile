# Stage 1: Build stage
FROM python:3.13-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime stage
FROM python:3.13-alpine

# Install runtime dependencies only
RUN apk add --no-cache libffi

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY glycol/ /app/glycol/
COPY web_server.py /app/
COPY README.md /app/
COPY CHANGELOG.md /app/

# Create directories for logs and credentials
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8666
ENV HOST=0.0.0.0

# Expose port (configurable via ENV)
EXPOSE ${PORT}

# Health check (liveness probe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8666/healthz/live || exit 1

# Run as non-root user
RUN adduser -D -u 1000 glycol && \
    chown -R glycol:glycol /app
USER glycol

# Entrypoint
ENTRYPOINT ["python", "web_server.py"]

# Default command - can be overridden
CMD ["--host", "0.0.0.0", "--port", "8666"]
