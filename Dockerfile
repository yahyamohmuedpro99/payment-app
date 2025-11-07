FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . /app/

# Create directory for logs
RUN mkdir -p /app/logs

# Collect static files will be run via docker-compose command
# RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Default command (will be overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
