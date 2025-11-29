# SPDX-License-Identifier: MIT
# scripts/download_model.py
import os
import requests

MODEL_URL = "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.onnx"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "../models")
MODEL_PATH = os.path.join(MODEL_DIR, "vehicle_person_uav.onnx")

def download_model():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    
    print(f"Downloading model from {MODEL_URL}...")
    response = requests.get(MODEL_URL, stream=True)
    response.raise_for_status()
    
    with open(MODEL_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    download_model()
