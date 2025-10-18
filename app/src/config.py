# SPDX-License-Identifier: MIT
import os

CONF_THRESH = float(os.getenv("CONF_THRESH", "0.5"))
NMS_THRESH = float(os.getenv("NMS_THRESH", "0.45"))
CLASSES = [c.strip() for c in os.getenv("CLASSES", "person,vehicle,drone,excavator").split(",")]
STREAM_SOURCE = os.getenv("STREAM_SOURCE", "payload_camera")  # or local_dir
INCLUDE_IR = os.getenv("INCLUDE_IR", "true").lower() == "true"
ALERT_TOPIC = os.getenv("ALERT_TOPIC", "orbital/anomalies")
MAX_PAYLOAD_KB = int(os.getenv("MAX_PAYLOAD_KB", "32"))
SIGNING_KEY = os.getenv("SIGNING_KEY", "dev-secret")  # replace with KeyVault injection in production
FACILITY_ID = os.getenv("FACILITY_ID", "")  # optional fixed facility tag
