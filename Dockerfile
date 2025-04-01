# Use a lighter base image, like python:3.11-slim-buster
FROM python:3.13-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=2.1.1
ENV POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip \
    && pip install "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock /app/

# Install all dependencies including runtime and development
RUN poetry install --no-root

# Stage 2: Production stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

ENV PYTHONPATH=/app

# Copy only the necessary files from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the content of your source directory to the /app directory
COPY src/project_name project_name

# Run the Flask application
ENTRYPOINT ["python", "project_name/main.py"]
