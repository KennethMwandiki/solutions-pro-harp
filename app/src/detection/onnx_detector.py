# SPDX-License-Identifier: MIT
# src/onnx_detector.py
import onnxruntime as ort
import numpy as np
from typing import List, Dict

CLASSES = ["person", "vehicle", "drone", "excavator", "flood"]

class OnnxDetector:
    def __init__(self, model_path: str, providers=None):
        self.session = ort.InferenceSession(model_path, providers=providers or ["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def preprocess(self, image, size=(640,640)):
        import cv2
        img = cv2.resize(image, size)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2,0,1)[None, ...]
        return img

    def postprocess(self, preds: np.ndarray, conf_thresh=0.5) -> List[Dict]:
        results = []
        for det in preds:
            x1,y1,x2,y2,conf,cls = det
            if conf < conf_thresh: continue
            results.append({
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": float(conf),
                "class_id": int(cls),
                "class_name": CLASSES[int(cls)] if int(cls) < len(CLASSES) else f"class_{cls}"
            })
        return results

    def detect(self, image) -> List[Dict]:
        blob = self.preprocess(image)
        preds = self.session.run([self.output_name], {self.input_name: blob})[0]
        return self.postprocess(preds.squeeze())