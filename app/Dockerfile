# SPDX-License-Identifier: MIT
# Minimal ONNX Runtime container for orbital inference

FROM python:3.11-slim

# System deps for ONNX and image ops
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src
COPY models/ /app/models

# Runtime configuration via env
ENV CONF_THRESH=0.5
ENV NMS_THRESH=0.45
ENV CLASSES="person,vehicle,drone,excavator"
ENV STREAM_SOURCE=payload_camera
ENV INCLUDE_IR=true
ENV ALERT_TOPIC=orbital/anomalies
ENV MAX_PAYLOAD_KB=32

# Health/entrypoint
CMD ["python", "src/main.py"]
