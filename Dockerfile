# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Install uv (ultraviolet) as package manager
RUN pip install --upgrade pip && pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies with uv
RUN uv pip install --system --requirement pyproject.toml

# Copy the rest of the code
COPY . /app/

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Run migrations, then start FastAPI
ENTRYPOINT ["/app/entrypoint.sh"]
