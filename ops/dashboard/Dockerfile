# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
# Note: We assume the context is the project root to include ops.emergency
COPY ops/dashboard/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the dashboard code
COPY ops/dashboard/ ./ops/dashboard/
# Copy the emergency logic (dependency)
COPY ops/emergency/ ./ops/emergency/

# Set Python path to find the ops modules
ENV PYTHONPATH=/app

# Expose Streamlit port
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Entry point for the dashboard
ENTRYPOINT ["streamlit", "run", "ops/dashboard/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
