# Use Python 3.13 slim image
FROM python:3.13-slim

# Set labels for the image
LABEL maintainer="GRC Agent Squad Team"
LABEL description="GRC Agent Squad - AI agents specialized for Governance, Risk Management, and Compliance"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash grcagent && \
    chown -R grcagent:grcagent /app
USER grcagent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run the application
CMD ["python", "-m", "src.main"] 