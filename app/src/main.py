# SPDX-License-Identifier: MIT
import time
from adapters.frame_stream import FrameStream
from adapters.secure_alert_sink import SecureAlertSink
from adapters.geo import embed_geo
from detection.pipeline import OnnxPipeline
from utils.logging import get_logger
from config import FACILITY_ID

log = get_logger("main")

def build_alerts(detections, meta, facility_id):
    geo = embed_geo(meta, facility_id)
    alerts = []
    for d in detections:
        alerts.append({
            "timestamp": meta.get("timestamp"),
            "anomaly_type": d["class_name"],
            "confidence": d["confidence"],
            "bbox": d["bbox"],
            "geo": geo
        })
    return alerts

def run():
    pipeline = OnnxPipeline("models/vehicle_person_uav.onnx")
    sink = SecureAlertSink()

    for frame in FrameStream():
        if frame is None:
            time.sleep(1.0)
            continue
        detections = pipeline.process(frame.image)
        if detections:
            alerts = build_alerts(detections, frame.meta, FACILITY_ID)
            sink.send(alerts)

if __name__ == "__main__":
    log.info("Starting orbital inference container...")
    run()
