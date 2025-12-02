# SPDX-License-Identifier: MIT
# src/framestream.py
import cv2, time
from typing import Iterator, Dict

class Frame:
    def __init__(self, image, meta: Dict):
        self.image = image
        self.meta = meta

class FrameStream:
    def __init__(self, source=0, image_path=None):
        self.image_path = image_path
        if not self.image_path:
            self.cap = cv2.VideoCapture(source)

    def stream(self) -> Iterator[Frame]:
        while True:
            if self.image_path:
                frame = cv2.imread(self.image_path)
                if frame is None:
                    raise FileNotFoundError(f"Could not read image: {self.image_path}")
                time.sleep(1) # Simulate 1fps
            else:
                ret, frame = self.cap.read()
                if not ret:
                    break
            
            meta = {
                "timestamp": time.time(),
                "latitude": 47.6062, # Seattle
                "longitude": -122.3321,
                "altitude": 550000,
                "orbitId": "ORB-23",
                "facility_id": "FAC-001"
            }
            yield Frame(frame, meta)