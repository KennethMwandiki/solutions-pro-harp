# SPDX-License-Identifier: MIT
import json
import os
from typing import Dict, List
from ..utils.logging import get_logger
from ..utils.security import sign_payload
from ..config import MAX_PAYLOAD_KB, SIGNING_KEY, ALERT_TOPIC

log = get_logger("secure_alert_sink")

class SecureAlertSink:
    def __init__(self, topic: str = ALERT_TOPIC):
        self.topic = topic
        # Replace with SDK host messaging client in production

    def send(self, alerts: List[Dict]):
        # Minimal payload: small, signed packet(s)
        payload = {
            "topic": self.topic,
            "count": len(alerts),
            "alerts": alerts,
        }
        serialized = json.dumps(payload, separators=(",", ":"))
        kb = len(serialized.encode("utf-8")) / 1024.0
        if kb > MAX_PAYLOAD_KB:
            log.warning("Payload exceeds size limit (%.2f KB > %d KB). Trimming thumbnails...", kb, MAX_PAYLOAD_KB)
            for a in alerts:
                a.pop("thumb", None)
            serialized = json.dumps({"topic": self.topic, "count": len(alerts), "alerts": alerts}, separators=(",", ":"))

        signature = sign_payload(payload, SIGNING_KEY)
        envelope = {"payload": json.loads(serialized), "signature": signature}

        # Stub: print. Replace with secure downlink publish.
        log.info("Sending %d alert(s) to topic=%s size=%.2f KB", len(alerts), self.topic, kb)
        print(json.dumps(envelope))
