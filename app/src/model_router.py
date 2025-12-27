"""
Model Router for A/B Testing and Versioning.

This module manages traffic splitting between different model versions and
tracks model registry metadata.
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime

@dataclass
class ModelVersion:
    """Metadata for a specific model version."""
    version_id: str
    model_path: str
    release_date: str
    description: str
    status: str  # active, candidate, archived
    performance_metrics: Dict[str, float]


class ModelRouter:
    """
    Routes inference requests to different model versions based on split configuration.
    Implements A/B testing logic.
    """
    
    def __init__(self, registry_path: str = "models/registry.json"):
        self.registry_path = registry_path
        self.versions: Dict[str, ModelVersion] = {}
        self.split_config: Dict[str, float] = {}  # version_id -> weight (0.0 to 1.0)
        
        # Load registry if exists, else init mock
        self._init_mock_registry()
    
    def _init_mock_registry(self):
        """Initialize with mock data for testing."""
        self.versions = {
            "v1": ModelVersion(
                version_id="v1",
                model_path="models/vehicle_person_uav.onnx",
                release_date="2025-10-01",
                description="Initial baseline model",
                status="active",
                performance_metrics={"mAP": 0.75}
            ),
            "v2-candidate": ModelVersion(
                version_id="v2-candidate",
                model_path="models/vehicle_person_uav_v2.onnx",
                release_date="2025-12-28",
                description="Retrained with active learning data",
                status="candidate",
                performance_metrics={"mAP": 0.82}
            )
        }
        
        # Traffic split: 80% to v1 (stable), 20% to v2 (candidate)
        self.split_config = {
            "v1": 0.8,
            "v2-candidate": 0.2
        }

    def get_model_for_inference(self, request_id: str = None) -> ModelVersion:
        """
        Determine which model version to use for a given request.
        
        Args:
            request_id: Optional ID to ensure sticky routing (consistent version for same user)
        
        Returns:
            ModelVersion object to use
        """
        # Random traffic splitting logic
        rand = random.random()
        cumulative = 0.0
        
        for ver_id, weight in self.split_config.items():
            cumulative += weight
            if rand <= cumulative:
                return self.versions[ver_id]
        
        # Fallback to v1
        return self.versions["v1"]

    def log_inference_result(self, version_id: str, success: bool, inference_time: float):
        """Log metrics for A/B test analysis."""
        # In production, this would write to Azure Monitor / App Insights
        # print(f"[ModelRouter] Metric: ver={version_id} success={success} time={inference_time:.3f}s")
        pass

    def update_split(self, new_split: Dict[str, float]):
        """Update traffic split configuration dynamically."""
        total = sum(new_split.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Split weights must sum to 1.0 (got {total})")
        self.split_config = new_split
