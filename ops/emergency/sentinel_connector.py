"""
Azure Sentinel Connector.

This module handles the ingestion of alerts from Azure Sentinel (Log Analytics)
and converts them into standard ThreatEvent objects for the emergency system.
"""

import os
import time
import uuid
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Conditional import for real Azure libraries
try:
    from azure.identity import DefaultAzureCredential
    from azure.monitor.query import LogsQueryClient, LogsQueryStatus
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

from ops.emergency.data_models import ThreatEvent, ThreatType, GeoLocation

class SentinelConnector:
    """Connects to Azure Sentinel workspace to fetch security alerts."""

    def __init__(self, workspace_id: Optional[str] = None):
        self.workspace_id = workspace_id or os.getenv("SENTINEL_WORKSPACE_ID")
        self.mock_mode = not (AZURE_AVAILABLE and self.workspace_id)
        self.client = None
        
        if not self.mock_mode:
            try:
                credential = DefaultAzureCredential()
                self.client = LogsQueryClient(credential)
            except Exception as e:
                print(f"Failed to initialize Azure client: {e}. Falling back to Mock Mode.")
                self.mock_mode = True

    def fetch_recent_alerts(self, lookback_minutes: int = 5) -> List[ThreatEvent]:
        """
        Fetch High severity alerts from the last N minutes.
        """
        if self.mock_mode:
            return self._fetch_mock_alerts()
        else:
            return self._fetch_real_alerts(lookback_minutes)

    def _fetch_real_alerts(self, lookback_minutes: int) -> List[ThreatEvent]:
        """Query Azure Log Analytics for SecurityAlert table."""
        if not self.client or not self.workspace_id:
            return []

        query = """
        SecurityAlert
        | where TimeGenerated > ago(5m)
        | where AlertSeverity == 'High'
        | project TimeGenerated, AlertName, AlertType, Description, Entities
        """
        
        try:
            # Note: Verify lookback logic match query or python arg
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=timedelta(minutes=lookback_minutes)
            )
            
            if response.status == LogsQueryStatus.PARTIAL:
                print("Warning: Sentinel query returned partial results.")
            
            events = []
            for row in response.tables[0].rows:
                # Basic mapping - in production needed robust Entity parsing for Location
                events.append(ThreatEvent(
                    id=f"sentinel-{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.now(), # Using fetch time for simplicity or row['TimeGenerated']
                    threat_type=ThreatType.SECURITY,
                    location=GeoLocation(40.7128, -74.0060), # Default to center if no entity loc
                    magnitude=8.0,
                    source="Azure Sentinel",
                    metadata={
                        "alert_name": row['AlertName'],
                        "description": row['Description']
                    }
                ))
            return events

        except Exception as e:
            print(f"Error querying Sentinel: {e}")
            return []

    def _fetch_mock_alerts(self) -> List[ThreatEvent]:
        """Generate simulated alerts for testing."""
        # Random chance to generate an alert
        if random.random() > 0.3: # 30% chance per poll
            return []
            
        alert_types = [
            ("Brute Force Attack", ThreatType.SECURITY),
            ("Malware Detected", ThreatType.SECURITY),
            ("Suspicious Drone Signal", ThreatType.SECURITY),
            ("Fire Alarm Sensor", ThreatType.FIRE)
        ]
        
        selection = random.choice(alert_types)
        
        # Random location shift around a center point
        lat = 40.7128 + (random.random() - 0.5) * 0.01
        lon = -74.0060 + (random.random() - 0.5) * 0.01
        
        return [ThreatEvent(
            id=f"mock-sentinel-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
            threat_type=selection[1],
            location=GeoLocation(lat, lon),
            magnitude=round(random.uniform(5.0, 9.0), 1),
            source="Mock Sentinel",
            metadata={
                "alert_name": selection[0],
                "description": f"Simulated {selection[0]} from Mock Connector",
                "simulated": True
            }
        )]
