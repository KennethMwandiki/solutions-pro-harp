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
        
        # Check if model expects float16
        input_type = self.session.get_inputs()[0].type
        if "float16" in input_type:
            img = img.astype(np.float16)
            
        return img

    def postprocess(self, preds: np.ndarray, conf_thresh=0.5) -> List[Dict]:
        results = []
        # preds shape is likely (1, 25200, 85) or (25200, 85)
        if preds.ndim == 3:
            preds = preds[0]
            
        for det in preds:
            # YOLOv5 raw output: cx, cy, w, h, obj_conf, class_scores...
            if len(det) < 6: continue
            
            obj_conf = det[4]
            if obj_conf < conf_thresh: continue
            
            class_scores = det[5:]
            class_id = np.argmax(class_scores)
            class_conf = class_scores[class_id]
            conf = obj_conf * class_conf
            
            if conf < conf_thresh: continue
            
            cx, cy, w, h = det[0], det[1], det[2], det[3]
            x1 = cx - w/2
            y1 = cy - h/2
            x2 = cx + w/2
            y2 = cy + h/2
            
            results.append({
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": float(conf),
                "class_id": int(class_id),
                "class_name": CLASSES[int(class_id)] if int(class_id) < len(CLASSES) else f"class_{class_id}"
            })
        
        # Simple NMS (optional, taking top 5 for now to avoid flood)
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:5]

    def detect(self, image) -> List[Dict]:
        blob = self.preprocess(image)
        preds = self.session.run([self.output_name], {self.input_name: blob})[0]
        return self.postprocess(preds.squeeze())