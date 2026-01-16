"""
Rule engine for threat evaluation, risk scoring, and escalation determination.

This module implements the core decision-making logic for the emergency response system.
"""

import yaml
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from ops.emergency.data_models import (
    ThreatEvent, ThreatType, EscalationLevel, CriticalityLevel,
    TrackedObject, Personnel, AreaOfInterest, GeoLocation
)
from ops.emergency.geo_utils import GeoUtils, Coordinate


class ConfigManager:
    """Manages system configuration."""
    
    def __init__(self, config_path: str):
        """
        Initialize config manager.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
    
    def get_threshold(self, threat_type: ThreatType, level: str) -> float:
        """Get magnitude threshold for a threat type and level."""
        return self.config["thresholds"][threat_type.value][level]
    
    def get_hotlines(self, threat_type: ThreatType) -> Dict[str, str]:
        """Get hotline map for a threat type."""
        return self.config["hotlines"][threat_type.value]
    
    def get_escalation_contacts(self, threat_type: ThreatType, level: EscalationLevel) -> List[str]:
        """Get contact keys for a threat type and escalation level."""
        return self.config["escalation_matrix"][threat_type.value][level.value]
    
    def get_risk_weights(self) -> Dict[str, float]:
        """Get risk scoring weights."""
        return self.config["risk_scoring"]
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings."""
        return self.config["notifications"]


class RiskScorer:
    """Calculates risk scores for threat events."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize risk scorer.
        
        Args:
            config: Configuration manager
        """
        self.config = config
        self.weights = config.get_risk_weights()
    
    def calculate_risk_score(
        self,
        event: ThreatEvent,
        entity_criticality: float,  # 0.0 to 1.0
        entity_vulnerability: float,  # 0.0 to 1.0
        distance_km: float
    ) -> float:
        """
        Calculate risk score for an event affecting an entity.
        
        Args:
            event: Threat event
            entity_criticality: Entity criticality (normalized 0-1)
            entity_vulnerability: Entity vulnerability (0-1)
            distance_km: Distance from event to entity
            
        Returns:
            Risk score (0-10)
        """
        # Normalize magnitude to 0-1 (assume max magnitude is 10)
        normalized_magnitude = min(event.magnitude / 10.0, 1.0)
        
        # Proximity score - inverse of distance (closer = higher risk)
        # Use exponential decay with 10km half-life
        proximity_score = 2 ** (-distance_km / 10.0)
        
        # Weighted sum
        risk_score = (
            normalized_magnitude * self.weights["magnitude_weight"] +
            entity_criticality * self.weights["criticality_weight"] +
            entity_vulnerability * self.weights["vulnerability_weight"] +
            proximity_score * self.weights["proximity_weight"]
        )
        
        # Scale to 0-10
        return risk_score * 10.0
    
    def calculate_object_risk(self, event: ThreatEvent, obj: TrackedObject, distance_km: float) -> float:
        """Calculate risk score for an object."""
        criticality_normalized = obj.criticality.value / 4.0  # CriticalityLevel max is 4
        return self.calculate_risk_score(
            event,
            criticality_normalized,
            obj.vulnerability_score,
            distance_km
        )
    
    def calculate_personnel_risk(self, event: ThreatEvent, person: Personnel, distance_km: float) -> float:
        """Calculate risk score for personnel."""
        criticality_normalized = person.criticality.value / 4.0
        # Personnel vulnerability is based on whether they have safety clearance
        has_clearance = event.threat_type.value in person.safety_clearances
        vulnerability = 0.3 if has_clearance else 0.8
        return self.calculate_risk_score(
            event,
            criticality_normalized,
            vulnerability,
            distance_km
        )


class EscalationDeterminer:
    """Determines escalation level based on event magnitude and risk score."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize escalation determiner.
        
        Args:
            config: Configuration manager
        """
        self.config = config
    
    def determine_level(self, event: ThreatEvent, max_risk_score: float) -> EscalationLevel:
        """
        Determine escalation level.
        
        Args:
            event: Threat event
            max_risk_score: Maximum risk score across all affected entities
            
        Returns:
            Escalation level
        """
        # Get thresholds for this threat type
        try:
            low_threshold = self.config.get_threshold(event.threat_type, "low")
            medium_threshold = self.config.get_threshold(event.threat_type, "medium")
            high_threshold = self.config.get_threshold(event.threat_type, "high")
        except KeyError:
            # Default to medium if threat type not configured
            return EscalationLevel.MEDIUM
        
        # Use both magnitude and risk score for determination
        combined_score = (event.magnitude + max_risk_score) / 2.0
        
        if combined_score >= high_threshold:
            return EscalationLevel.HIGH
        elif combined_score >= medium_threshold:
            return EscalationLevel.MEDIUM
        else:
            return EscalationLevel.LOW


class CircuitBreaker:
    """Prevents notification spam by tracking event frequency."""
    
    def __init__(self, debounce_window_seconds: int, max_events_per_window: int):
        """
        Initialize circuit breaker.
        
        Args:
            debounce_window_seconds: Time window for debouncing
            max_events_per_window: Max events allowed in window
        """
        self.debounce_window = timedelta(seconds=debounce_window_seconds)
        self.max_events = max_events_per_window
        self.event_history: Dict[str, List[datetime]] = defaultdict(list)
    
    def should_process(self, event_key: str) -> bool:
        """
        Check if an event should be processed or rate-limited.
        
        Args:
            event_key: Unique key for the event (e.g., f"{threat_type}:{location_hash}")
            
        Returns:
            True if event should be processed
        """
        now = datetime.now()
        
        # Clean up old events
        cutoff = now - self.debounce_window
        self.event_history[event_key] = [
            ts for ts in self.event_history[event_key] if ts > cutoff
        ]
        
        # Check if we've exceeded the limit
        if len(self.event_history[event_key]) >= self.max_events:
            return False
        
        # Record this event
        self.event_history[event_key].append(now)
        return True


class RuleEngine:
    """Main rule engine for processing threat events."""
    
    def __init__(self, config_path: str):
        """
        Initialize rule engine.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigManager(config_path)
        self.risk_scorer = RiskScorer(self.config)
        self.escalation_determiner = EscalationDeterminer(self.config)
        
        # Initialize circuit breaker
        notif_settings = self.config.get_notification_settings()
        cb_settings = notif_settings.get("circuit_breaker", {})
        if cb_settings.get("enabled", True):
            self.circuit_breaker = CircuitBreaker(
                cb_settings.get("debounce_window_seconds", 300),
                cb_settings.get("max_events_per_window", 5)
            )
        else:
            self.circuit_breaker = None
    
    def evaluate_event(
        self,
        event: ThreatEvent,
        objects: List[TrackedObject],
        personnel: List[Personnel],
        areas: List[AreaOfInterest],
        active_perimeter: Optional[List[Tuple[float, float]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate a threat event against entities.
        
        Args:
            event: Threat event to evaluate
            objects: List of tracked objects
            personnel: List of personnel
            areas: List of areas of interest
            active_perimeter: Optional perimeter polygon to check event location
            
        Returns:
            Evaluation result dictionary or None if event should be ignored
        """
        # Check if event is within active perimeter
        if active_perimeter:
            event_coord = Coordinate(event.location.lat, event.location.lon)
            if not GeoUtils.point_in_polygon(event_coord, active_perimeter):
                return None  # Ignore out-of-area events
        
        # Check circuit breaker
        if self.circuit_breaker:
            event_key = f"{event.threat_type.value}:{event.location.lat:.3f}:{event.location.lon:.3f}"
            if not self.circuit_breaker.should_process(event_key):
                return {
                    "rate_limited": True,
                    "event_id": event.id,
                    "message": "Event rate-limited by circuit breaker"
                }
        
        # Calculate risk scores for all entities
        affected_entities = []
        max_risk_score = 0.0
        
        # Evaluate objects
        for obj in objects:
            distance = GeoUtils.haversine_distance(
                Coordinate(event.location.lat, event.location.lon),
                Coordinate(obj.location.lat, obj.location.lon)
            )
            risk_score = self.risk_scorer.calculate_object_risk(event, obj, distance)
            
            if risk_score > 1.0:  # Threshold for "affected"
                affected_entities.append({
                    "type": "object",
                    "id": obj.id,
                    "name": obj.name,
                    "distance_km": distance,
                    "risk_score": risk_score
                })
                max_risk_score = max(max_risk_score, risk_score)
        
        # Evaluate personnel
        for person in personnel:
            distance = GeoUtils.haversine_distance(
                Coordinate(event.location.lat, event.location.lon),
                Coordinate(person.location.lat, person.location.lon)
            )
            risk_score = self.risk_scorer.calculate_personnel_risk(event, person, distance)
            
            if risk_score > 1.0:
                affected_entities.append({
                    "type": "personnel",
                    "id": person.id,
                    "name": person.name,
                    "role": person.role,
                    "distance_km": distance,
                    "risk_score": risk_score,
                    "contact_phone": person.contact_phone,
                    "on_duty": person.on_duty
                })
                max_risk_score = max(max_risk_score, risk_score)
        
        # Evaluate areas
        for area in areas:
            # Check if event is within this area
            event_coord = Coordinate(event.location.lat, event.location.lon)
            if GeoUtils.point_in_polygon(event_coord, area.polygon_coords):
                # Calculate a risk score based on area properties
                area_risk = (
                    event.magnitude * 0.5 +
                    area.population_density / 1000.0 * 0.3 +
                    area.strategic_importance.value / 4.0 * 0.2
                )
                affected_entities.append({
                    "type": "area",
                    "id": area.id,
                    "name": area.name,
                    "risk_score": area_risk,
                    "population_density": area.population_density,
                    "available_resources": area.available_resources
                })
                max_risk_score = max(max_risk_score, area_risk)
        
        # If no entities are affected, ignore event
        if not affected_entities:
            return None
        
        # Determine escalation level
        escalation_level = self.escalation_determiner.determine_level(event, max_risk_score)
        
        # Get contact list
        contacts = self.config.get_escalation_contacts(event.threat_type, escalation_level)
        hotlines = self.config.get_hotlines(event.threat_type)
        contact_numbers = [hotlines.get(c, "UNKNOWN") for c in contacts]
        
        return {
            "event_id": event.id,
            "threat_type": event.threat_type.value,
            "magnitude": event.magnitude,
            "location": event.location.to_dict(),
            "max_risk_score": max_risk_score,
            "escalation_level": escalation_level.value,
            "affected_entities": affected_entities,
            "contacts_to_notify": contacts,
            "contact_numbers": contact_numbers
        }
