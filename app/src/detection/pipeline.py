# SPDX-License-Identifier: MIT
from typing import List, Dict
import cv2
from .onnx_detector import OnnxDetector

class OnnxPipeline:
    def __init__(self, model_path: str):
        self.detector = OnnxDetector(model_path)

    def process(self, image) -> List[Dict]:
        results = self.detector.infer(image)
        # Optionally attach thumbnails to each result (will be trimmed if payload too large)
        thumb = self._thumbnail(image)
        for r in results:
            r["thumb"] = thumb
        return results

    def _thumbnail(self, image, size=(160, 160)):
        t = cv2.resize(image, size)
        # For compact payloads, store thumbnail as summary stats instead of raw pixels
        # In production, consider JPEG base64 with payload size guard
        return {"w": size[0], "h": size[1]}
