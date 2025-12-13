# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/python:3.12-slim

# Build arguments for pip configuration
ARG PIP_DEFAULT_TIMEOUT=300
ARG PIP_RETRIES=5

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT}
ENV PIP_RETRIES=${PIP_RETRIES}
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml requirements.txt ./

# Install Python dependencies directly with pip (more reliable in restricted networks)
RUN pip install --upgrade pip && \
    pip install --timeout=300 --retries=5 -r requirements.txt

# Copy the rest of the code
COPY . /app/

# Expose port
EXPOSE 8000

# Start FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
