# SPDX-License-Identifier: MIT
# src/framestream.py
import cv2, time
from typing import Iterator, Dict

class Frame:
    def __init__(self, image, meta: Dict):
        self.image = image
        self.meta = meta

class FrameStream:
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)

    def stream(self) -> Iterator[Frame]:
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            meta = {
                "timestamp": time.time(),
                "latitude": -0.289,
                "longitude": 37.893,
                "altitude": 550000,
                "orbitId": "ORB-23",
                "facility_id": "DC-NAIROBI-01"
            }
            yield Frame(frame, meta)