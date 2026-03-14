# Multi-stage build for PlanetHack CTF Tool

# Stage 1: Python base
FROM python:3.11-slim as python-base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nmap \
    git \
    curl \
    wget \
    sqlmap \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (no xvfb -- web mode doesn't need X11)
RUN apt-get update && apt-get install -y \
    nmap \
    git \
    curl \
    wget \
    sqlmap \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Copy application code
COPY python/ ./python/
COPY config/ ./config/
COPY main.py .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Default: web UI mode (browser-accessible)
CMD ["python", "main.py", "--web", "--host", "0.0.0.0", "--port", "8080"]
