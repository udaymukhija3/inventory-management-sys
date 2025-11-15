# Multi-stage build for optimization
FROM python:3.11-slim AS build

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Copy installed packages from build stage to user's home
COPY --from=build /root/.local /home/appuser/.local
RUN chown -R appuser:appuser /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create directories for data and models
RUN mkdir -p /app/data /app/models && \
    chown -R appuser:appuser /app/data /app/models

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

CMD ["python", "data_pipeline.py"]

