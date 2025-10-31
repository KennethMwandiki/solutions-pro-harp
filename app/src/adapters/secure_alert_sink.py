# SPDX-License-Identifier: MIT
# src/secure_alert_sink.py
import jwt, requests, time
from typing import List, Dict

class SecureAlertSink:
    def __init__(self, endpoint: str, secret: str):
        self.endpoint = endpoint
        self.secret = secret

    def send(self, detections: List[Dict], meta: Dict):
        payload = {
            "topic": "proharp/anomalies",
            "count": len(detections),
            "alerts": []
        }
        for d in detections:
            payload["alerts"].append({
                "timestamp": meta["timestamp"],
                "anomaly_type": d["class_name"],
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "geo": {
                    "latitude": meta["latitude"],
                    "longitude": meta["longitude"],
                    "altitude": meta["altitude"],
                    "orbitId": meta["orbitId"],
                    "facility_id": meta["facility_id"],
                    "telemetry_source": "auto",
                    "manual_override": {"enabled": False, "latitude": None, "longitude": None, "reason": None}
                }
            })
        token = jwt.encode(payload, self.secret, algorithm="HS256")
        envelope = {"payload": payload, "signature": token}
        r = requests.post(self.endpoint, json=envelope, timeout=10)
        return r.status_code