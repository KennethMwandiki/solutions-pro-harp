"""
Active Learning Data Collector.

This module manages the collection of interesting frames (low confidence, edge cases)
for model retraining.
"""

import os
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class ActiveLearningCollector:
    def __init__(self, storage_dir: str = "active_learning_data"):
        """
        Initialize the collector.
        
        Args:
            storage_dir: Local directory to stage images before upload to Azure
        """
        self.storage_dir = Path(storage_dir)
        self.images_dir = self.storage_dir / "images"
        self.metadata_dir = self.storage_dir / "metadata"
        
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Thresholds for "uncertainty sampling"
        self.min_conf = 0.4
        self.max_conf = 0.7

    def check_and_collect(self, frame_image: Any, detections: List[Dict[str, Any]], meta: Dict[str, Any]) -> bool:
        """
        Check if a frame is interesting for active learning and save it if so.
        
        Args:
            frame_image: The raw image object (or path)
            detections: List of detection dicts (label, confidence, bbox)
            meta: Metadata about the frame
            
        Returns:
            True if collected, False otherwise
        """
        should_collect = False
        reason = "none"
        
        # 1. Uncertainty Sampling
        # If any detection has confidence in the "uncertain" range
        for det in detections:
            conf = det.get("confidence", 0)
            if self.min_conf <= conf <= self.max_conf:
                should_collect = True
                reason = f"uncertainty_sampling_conf_{conf:.2f}"
                break
        
        # 2. No Detections but high motion/energy? (Simulated logic)
        # In a real system, we'd check if we expected something but got nothing.
        
        if should_collect:
            self._save_sample(frame_image, detections, meta, reason)
            return True
            
        return False

    def _save_sample(self, image, detections, meta, reason):
        """Save the sample to disk."""
        sample_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Save Metadata
        metadata = {
            "id": sample_id,
            "timestamp": timestamp,
            "reason": reason,
            "detections": detections,
            "original_meta": meta
        }
        
        with open(self.metadata_dir / f"{sample_id}.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Save Image (Mocking the save since 'image' type depends on CV2 or PIL)
        # In real impl, use cv2.imwrite(path, image)
        # Here we just touch a file if string, or ignore
        img_path = self.images_dir / f"{sample_id}.jpg"
        if isinstance(image, str) and os.path.exists(image):
            shutil.copy(image, img_path)
        else:
            # Create dummy placeholder for demo
            with open(img_path, "w") as f:
                f.write("binary_image_data_placeholder")
                
        print(f"[ActiveLearning] Collected sample {sample_id} ({reason})")

    def sync_to_cloud(self, container_name: str = "model-refinement"):
        """
        Mock function to upload staged data to Azure Blob Storage.
        """
        count = len(list(self.metadata_dir.glob("*.json")))
        print(f"[ActiveLearning] Syncing {count} samples to Azure Blob container '{container_name}'...")
        # Azure Blob upload logic would go here
        return count
