# Dockerfile

# Use an official Python runtime as a parent image
# Choose a version compatible with your project (e.g., 3.11, 3.12)
# Using 3.11 based on the tutorial example
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1  # Prevents python from writing .pyc files
ENV PYTHONUNBUFFERED 1         # Prevents python from buffering stdout/stderr

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., for psycopg2)
# Sometimes necessary, depends on the base image. Slim images often need this.
# Uncomment the line below if you encounter psycopg2 install issues during build
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project source code into the container
# Ensure your .dockerignore file excludes unnecessary files/dirs like .git, venv, etc.
# (We will create .dockerignore in the next step)
COPY src/ .

# Run collectstatic
# This gathers all static files (CSS, JS, images) into the STATIC_ROOT directory
# WhiteNoise will then serve these files efficiently.
RUN python manage.py collectstatic --noinput

# Gunicorn is installed via requirements.txt

# Expose the port Gunicorn will run on (Cloud Run expects 8080 by default)
EXPOSE 8080

# Define the command to run your application using Gunicorn
# -w 2: Number of worker processes (adjust based on instance size, start low)
# --threads 4: Threads per worker
# -b 0.0.0.0:8080: Bind to all network interfaces on port 8080
# core.wsgi: Path to your WSGI application module (relative to WORKDIR /app)
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--bind", "0.0.0.0:8080", "core.wsgi"]