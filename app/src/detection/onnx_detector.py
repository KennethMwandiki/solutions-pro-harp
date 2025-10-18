# SPDX-License-Identifier: MIT
import numpy as np
import onnxruntime as ort
import cv2
from typing import List, Dict, Tuple
from ..utils.logging import get_logger
from ..config import CONF_THRESH, NMS_THRESH, CLASSES

log = get_logger("onnx_detector")

class OnnxDetector:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.out_names = [o.name for o in self.session.get_outputs()]
        log.info("ONNX model loaded: %s", model_path)

    def preprocess(self, img: np.ndarray, size: Tuple[int, int]=(640, 640)) -> Tuple[np.ndarray, float, Tuple[int,int]]:
        h, w = img.shape[:2]
        scale = min(size[0] / h, size[1] / w)
        nh, nw = int(h * scale), int(w * scale)
        resized = cv2.resize(img, (nw, nh))
        canvas = np.full((size[0], size[1], 3), 114, dtype=np.uint8)
        canvas[:nh, :nw] = resized
        blob = canvas.astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)  # CHW
        blob = np.expand_dims(blob, axis=0)
        return blob, scale, (nw, nh)

    def postprocess(self, preds: np.ndarray, scale: float, scaled_size: Tuple[int,int], conf_thresh=CONF_THRESH, nms_thresh=NMS_THRESH):
        # Expecting output format: [N, 6] -> x1,y1,x2,y2,conf,class_id (example; adjust per your model)
        boxes, scores, labels = [], [], []
        for det in preds:
            x1, y1, x2, y2, conf, cls = det
            if conf < conf_thresh:
                continue
            boxes.append([x1/scale, y1/scale, x2/scale, y2/scale])
            scores.append(conf)
            labels.append(int(cls))
        if not boxes:
            return []

        keep = self.nms(np.array(boxes), np.array(scores), nms_thresh)
        results = []
        for i in keep:
            x1, y1, x2, y2 = boxes[i]
            cls_id = labels[i]
            cls_name = CLASSES[cls_id] if cls_id < len(CLASSES) else f"class_{cls_id}"
            results.append({
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": float(scores[i]),
                "class_id": int(cls_id),
                "class_name": cls_name
            })
        return results

    def nms(self, boxes: np.ndarray, scores: np.ndarray, iou_thres: float):
        idxs = scores.argsort()[::-1]
        keep = []
        while idxs.size > 0:
            i = idxs[0]
            keep.append(i)
            if idxs.size == 1:
                break
            ious = self.iou(boxes[i], boxes[idxs[1:]])
            idxs = idxs[1:][ious <= iou_thres]
        return keep

    def iou(self, box: np.ndarray, boxes: np.ndarray):
        x1 = np.maximum(box[0], boxes[:,0])
        y1 = np.maximum(box[1], boxes[:,1])
        x2 = np.minimum(box[2], boxes[:,2])
        y2 = np.minimum(box[3], boxes[:,3])

        inter = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        area1 = (box[2] - box[0]) * (box[3] - box[1])
        area2 = (boxes[:,2] - boxes[:,0]) * (boxes[:,3] - boxes[:,1])
        union = area1 + area2 - inter + 1e-6
        return inter / union

    def infer(self, img: np.ndarray) -> List[Dict]:
        blob, scale, scaled_size = self.preprocess(img)
        outputs = self.session.run(self.out_names, {self.input_name: blob})
        # If model returns single output
        preds = outputs[0].squeeze()
        if preds.ndim == 1:
            preds = np.expand_dims(preds, axis=0)
        return self.postprocess(preds, scale, scaled_size)
