# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Docker-in-Docker support
RUN apt-get update && apt-get install -y \
    docker.io \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application files
COPY main.py ./
COPY .prompts/ .prompts/
COPY run.sh ./

# Make run.sh executable
RUN chmod +x run.sh

# Create directory for reports
RUN mkdir -p /app/reports

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "main.py"]
