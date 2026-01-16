"""
Event processor - main integration point for the emergency response system.

This module ties together all components: event ingestion, rule evaluation,
notification dispatch, and audit logging.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import uuid

from ops.emergency.data_models import (
    ThreatEvent, ThreatType, IncidentRecord, EscalationLevel,
    GeoLocation, EntityRepository
)
from ops.emergency.rule_engine import RuleEngine
from ops.emergency.notifications import NotificationDispatcher


class IncidentLogger:
    """Logs incidents to JSONL files for audit trail."""
    
    def __init__(self, log_path: str = "logs/incidents.jsonl"):
        """
        Initialize incident logger.
        
        Args:
            log_path: Path to incident log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("IncidentLogger")
        self.logger.setLevel(logging.INFO)
    
    def log_incident(self, incident: IncidentRecord) -> None:
        """
        Log an incident to the JSONL file.
        
        Args:
            incident: Incident record to log
        """
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(incident.to_dict()) + "\n")
        
        self.logger.info(f"Logged incident {incident.id}: {incident.threat_type.value} "
                        f"(escalation: {incident.escalation_level.value})")
    
    def get_recent_incidents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent incidents from the log.
        
        Args:
            limit: Maximum number of incidents to return
            
        Returns:
            List of incident dictionaries
        """
        if not self.log_path.exists():
            return []
        
        incidents = []
        with open(self.log_path, 'r') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                incidents.append(json.loads(line))
        
        return incidents


class EventProcessor:
    """Main event processing pipeline."""
    
    def __init__(
        self,
        config_path: str = "ops/emergency/config.yaml",
        log_dir: str = "logs"
    ):
        """
        Initialize event processor.
        
        Args:
            config_path: Path to configuration file
            log_dir: Directory for log files
        """
        self.rule_engine = RuleEngine(config_path)
        self.notification_dispatcher = NotificationDispatcher(
            retry_attempts=self.rule_engine.config.get_notification_settings()["retry_attempts"],
            retry_delay_seconds=self.rule_engine.config.get_notification_settings()["retry_delay_seconds"],
            log_dir=log_dir
        )
        self.incident_logger = IncidentLogger(f"{log_dir}/incidents.jsonl")
        
        self.logger = logging.getLogger("EventProcessor")
        self.logger.setLevel(logging.INFO)
        
        # Set up console handler
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console)
    
    def process_event(
        self,
        event: ThreatEvent,
        entity_repo: EntityRepository,
        active_perimeter: Optional[List[List[float]]] = None
    ) -> Optional[IncidentRecord]:
        """
        Process a threat event through the full pipeline.
        
        Args:
            event: Threat event to process
            entity_repo: Repository of entities (objects, personnel, areas)
            active_perimeter: Optional perimeter polygon to check event location
            
        Returns:
            IncidentRecord if incident was triggered, None otherwise
        """
        self.logger.info(f"Processing event {event.id}: {event.threat_type.value} "
                        f"(magnitude: {event.magnitude})")
        
        # Evaluate event against entities
        evaluation = self.rule_engine.evaluate_event(
            event,
            list(entity_repo.objects.values()),
            list(entity_repo.personnel.values()),
            list(entity_repo.areas.values()),
            active_perimeter
        )
        
        if evaluation is None:
            self.logger.info(f"Event {event.id} did not trigger any alerts (out of area or no affected entities)")
            return None
        
        if evaluation.get("rate_limited"):
            self.logger.warning(f"Event {event.id} was rate-limited by circuit breaker")
            return None
        
        # Dispatch notifications
        self.logger.info(f"Event {event.id} triggered {evaluation['escalation_level'].upper()} escalation")
        notification_results = self.notification_dispatcher.dispatch_all(evaluation)
        
        # Create incident record
        incident = IncidentRecord(
            id=str(uuid.uuid4()),
            event_id=event.id,
            timestamp=event.timestamp,
            threat_type=event.threat_type,
            location=event.location,
            magnitude=event.magnitude,
            risk_score=evaluation["max_risk_score"],
            escalation_level=EscalationLevel[evaluation["escalation_level"].upper()],
            affected_entities=[e["id"] for e in evaluation["affected_entities"]],
            notifications_sent=[
                {
                    "type": notification_type,
                    "results": [
                        {
                            "recipient": r.recipient,
                            "success": r.success,
                            "timestamp": r.timestamp.isoformat(),
                            "error": r.error
                        }
                        for r in results
                    ]
                }
                for notification_type, results in notification_results.items()
            ],
            metadata={
                "contacts_to_notify": evaluation["contacts_to_notify"],
                "contact_numbers": evaluation["contact_numbers"]
            }
        )
        
        # Log incident
        self.incident_logger.log_incident(incident)
        
        self.logger.info(f"Incident {incident.id} processed successfully")
        
        return incident
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics from recent incidents.
        
        Returns:
            Statistics dictionary
        """
        recent_incidents = self.incident_logger.get_recent_incidents(limit=100)
        
        if not recent_incidents:
            return {
                "total_incidents": 0,
                "escalation_breakdown": {},
                "threat_type_breakdown": {}
            }
        
        escalation_counts = {}
        threat_type_counts = {}
        
        for incident in recent_incidents:
            escalation_level = incident["escalation_level"]
            threat_type = incident["threat_type"]
            
            escalation_counts[escalation_level] = escalation_counts.get(escalation_level, 0) + 1
            threat_type_counts[threat_type] = threat_type_counts.get(threat_type, 0) + 1
        
        return {
            "total_incidents": len(recent_incidents),
            "escalation_breakdown": escalation_counts,
            "threat_type_breakdown": threat_type_counts,
            "recent_incidents": recent_incidents[-5:]  # Last 5
        }


def example_usage():
    """Example usage of the event processor."""
    from ops.emergency.data_models import TrackedObject, Personnel, AreaOfInterest, CriticalityLevel
    from ops.emergency.geo_utils import PerimeterGenerator
    
    # Create example entities
    repo = EntityRepository()
    
    # Add a critical infrastructure object
    repo.add_object(TrackedObject(
        id="obj-001",
        name="Power Station Alpha",
        location=GeoLocation(40.7128, -74.0060),
        criticality=CriticalityLevel.CRITICAL,
        vulnerability_score=0.8,
        asset_value=1000000
    ))
    
    # Add personnel
    repo.add_personnel(Personnel(
        id="pers-001",
        name="John Doe",
        role="First Responder",
        location=GeoLocation(40.7200, -74.0100),
        criticality=CriticalityLevel.HIGH,
        on_duty=True,
        safety_clearances=["fire", "medical"],
        contact_phone="+1-555-0101"
    ))
    
    # Add area of interest
    perimeter_coords = PerimeterGenerator.from_single_point(40.7128, -74.0060, 5)
    repo.add_area(AreaOfInterest(
        id="area-001",
        name="Downtown District",
        polygon_coords=perimeter_coords["geometry"]["coordinates"][0],
        population_density=10000,
        historical_incident_count=15,
        strategic_importance=CriticalityLevel.HIGH,
        available_resources=["hospital", "fire_station"]
    ))
    
    # Create event processor
    processor = EventProcessor()
    
    # Create a threat event
    event = ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.FIRE,
        location=GeoLocation(40.7150, -74.0080),
        magnitude=6.5,
        source="sensor_network"
    )
    
    # Process the event
    incident = processor.process_event(event, repo)
    
    if incident:
        print(f"\n✅ Incident {incident.id} created")
        print(f"   Escalation: {incident.escalation_level.value}")
        print(f"   Risk Score: {incident.risk_score:.2f}")
        print(f"   Affected Entities: {len(incident.affected_entities)}")
    
    # Get statistics
    stats = processor.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total Incidents: {stats['total_incidents']}")
    print(f"   Escalation Breakdown: {stats['escalation_breakdown']}")


if __name__ == "__main__":
    example_usage()
