# SPDX-License-Identifier: MIT
# src/main.py
from adapters.frame_stream import FrameStream
from detection.onnx_detector import OnnxDetector
from adapters.secure_alert_sink import SecureAlertSink

def run():
    # Use mock image for testing
    stream = FrameStream(image_path="test_image.jpg") 
    detector = OnnxDetector("models/vehicle_person_uav.onnx")
    sink = SecureAlertSink(
        endpoint="http://localhost:5000/ingest", 
        secret="this-is-a-very-secure-secret-for-local-testing-only-12345"
    )

    for frame in stream.stream():
        detections = detector.detect(frame.image)
        if detections:
            status = sink.send(detections, frame.meta)
            print(f"Sent {len(detections)} detections, status={status}")

if __name__ == "__main__":
    run()