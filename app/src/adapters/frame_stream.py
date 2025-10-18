# SPDX-License-Identifier: MIT
import os
import glob
import cv2
from typing import Iterator, Dict
from ..utils.logging import get_logger
from ..config import STREAM_SOURCE, INCLUDE_IR

log = get_logger("frame_stream")

class Frame:
    def __init__(self, image, meta: Dict):
        self.image = image
        self.meta = meta

def FrameStream(source: str = STREAM_SOURCE) -> Iterator[Frame]:
    """
    Stubbed frame stream:
    - payload_camera: would read from SDK host services (replace in production)
    - local_dir: reads images from /tmp/frames/*.jpg for simulation
    """
    if source == "local_dir":
        files = sorted(glob.glob("/tmp/frames/*.jpg"))
        if not files:
            log.warning("No local frames found in /tmp/frames")
        for f in files:
            img = cv2.imread(f)
            meta = {
                "timestamp": os.path.getmtime(f),
                "latitude": -0.102,   # stub; replace with real telemetry
                "longitude": 34.761,  # stub; replace with real telemetry
                "altitude": 550000,
                "orbitId": "SIM-01",
                "ir": INCLUDE_IR
            }
            yield Frame(img, meta)
    else:
        # payload_camera stub; replace with SDK camera adapter
        log.info("Payload camera stream stub active; emitting no frames.")
        return
