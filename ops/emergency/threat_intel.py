"""
Threat Intelligence Integration.

This module provides an interface for external threat intelligence feeds and
contains implementations for Mock and AlienVault OTX.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import uuid
import os
import requests
import logging

from ops.emergency.data_models import ThreatType, GeoLocation

logger = logging.getLogger(__name__)

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


class AlienVaultOTXProvider(ThreatIntelProvider):
    """
    Integration with AlienVault Open Threat Exchange (OTX).
    Requires ALIENVAULT_OTX_KEY in environment variables.
    """
    
    BASE_URL = "https://otx.alienvault.com/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-OTX-API-KEY": self.api_key}
        self.provider_name = "AlienVault OTX"
        
    def get_latest_threats(self, limit: int = 10) -> List[ThreatIndicator]:
        """Fetch latest pulses (threats) from user's subscribed feeds."""
        try:
            # Get subscribed pulses (or general if no subscriptions)
            url = f"{self.BASE_URL}/pulses/subscribed?limit={limit}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"AlienVault API Error: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            results = data.get("results", [])
            
            indicators = []
            for pulse in results:
                # Map Pulse to ThreatIndicator
                # Pulses don't always have geo, use generic or skip
                # We'll map generic type based on tags
                tags = pulse.get("tags", [])
                t_type = ThreatType.SECURITY # Default
                if "malware" in tags: t_type = ThreatType.SECURITY
                
                # OTX Pulses are collections of IOCs, not necessarily geo-located events
                # We use them as broad indicators
                
                indicators.append(ThreatIndicator(
                    id=str(pulse.get("id")),
                    source=self.provider_name,
                    threat_type=t_type,
                    severity=0.7, # Default high for OTX
                    location=None, # OTX pulses are global usually
                    timestamp=datetime.strptime(pulse.get("created").split(".")[0], "%Y-%m-%dT%H:%M:%S") if pulse.get("created") else datetime.now(),
                    description=pulse.get("name", "Unknown Pulse"),
                    confidence=0.9,
                    raw_data={"tags": tags, "author": pulse.get("author_name")}
                ))
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to fetch from AlienVault: {e}")
            return []

    def enrich_event(self, event_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich event using OTX.
        If metadata contains IP or Domain, query OTX for it.
        """
        enrichment = {"source": self.provider_name, "findings": []}
        
        # Example: Check for 'ip_address' in metadata
        ip = metadata.get("ip_address")
        if ip:
            try:
                url = f"{self.BASE_URL}/indicators/IPv4/{ip}/general"
                response = requests.get(url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    enrichment["findings"].append({
                        "indicator": ip,
                        "pulses": data.get("pulse_info", {}).get("count", 0),
                        "reputation": data.get("reputation")
                    })
            except Exception as e:
                logger.warning(f"Failed to enrich IP {ip}: {e}")
                
        return enrichment
