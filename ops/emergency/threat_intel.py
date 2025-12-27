"""
Threat Intelligence Integration.

This module provides an interface for external threat intelligence feeds and
contains mock implementations for testing.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import random
import uuid

from ops.emergency.data_models import ThreatType, GeoLocation

@dataclass
class ThreatIndicator:
    """Represents a threat indicator from an external feed."""
    id: str
    source: str
    threat_type: ThreatType
    severity: float  # 0.0 to 1.0
    location: Optional[GeoLocation]
    timestamp: datetime
    description: str
    confidence: float
    raw_data: Dict[str, Any]


class ThreatIntelProvider(ABC):
    """Abstract base class for threat intelligence providers."""
    
    @abstractmethod
    def get_latest_threats(self, limit: int = 10) -> List[ThreatIndicator]:
        """Fetch latest threat indicators."""
        pass
    
    @abstractmethod
    def enrich_event(self, event_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich an internal event with external intelligence."""
        pass


class MockExternalFeed(ThreatIntelProvider):
    """Mock provider simulating external feeds like Recorded Future or CrowdStrike."""
    
    def __init__(self, provider_name: str = "Mock-Intel-Corp"):
        self.provider_name = provider_name
    
    def get_latest_threats(self, limit: int = 10) -> List[ThreatIndicator]:
        """Generate random threat indicators."""
        indicators = []
        for _ in range(limit):
            t_type = random.choice(list(ThreatType))
            severity = random.random()
            
            # Random location around NYC for testing
            lat = 40.7 + (random.random() - 0.5) * 0.1
            lon = -74.0 + (random.random() - 0.5) * 0.1
            
            indicators.append(ThreatIndicator(
                id=f"intel-{uuid.uuid4().hex[:8]}",
                source=self.provider_name,
                threat_type=t_type,
                severity=severity,
                location=GeoLocation(lat, lon),
                timestamp=datetime.now(),
                description=f"Automated intelligence report for {t_type.value}",
                confidence=0.85 + (random.random() * 0.1),
                raw_data={"cve": None, "actor": "unknown"}
            ))
        return indicators

    def enrich_event(self, event_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Mock enrichment logic."""
        return {
            "intel_source": self.provider_name,
            "risk_assessment": "elevated" if "critical" in str(metadata) else "standard",
            "related_actors": ["group-a", "group-b"] if random.random() > 0.7 else []
        }
