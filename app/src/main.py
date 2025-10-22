# SPDX-License-Identifier: MIT
# src/main.py
from adapters.frame_stream import FrameStream
from detection.onnx_detector import OnnxDetector
from adapters.secure_alert_sink import SecureAlertSink

def run():
    stream = FrameStream(source=0)  # replace with SDK camera adapter
    detector = OnnxDetector("models/vehicle_person_uav.onnx")
    sink = SecureAlertSink(endpoint="https://groundapi/ingest", secret="supersecret")

    for frame in stream.stream():
        detections = detector.detect(frame.image)
        if detections:
            status = sink.send(detections, frame.meta)
            print(f"Sent {len(detections)} detections, status={status}")

if __name__ == "__main__":
    run()