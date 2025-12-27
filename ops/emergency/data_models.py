"""
Data models for objects, personnel, and areas of interest.

This module defines the core data structures for the emergency response system.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import json


class EntityType(Enum):
    """Types of entities in the system."""
    OBJECT = "object"
    PERSONNEL = "personnel"
    AREA = "area"


class ThreatType(Enum):
    """Types of threats."""
    FIRE = "fire"
    MEDICAL = "medical"
    SECURITY = "security"
    RADIATION = "radiation"
    SEISMIC = "seismic"
    CHEMICAL = "chemical"
    WEATHER = "weather"
    UNKNOWN = "unknown"


class CriticalityLevel(Enum):
    """Criticality levels for prioritization."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class EscalationLevel(Enum):
    """Escalation levels for incident response."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class GeoLocation:
    """Geographic location."""
    lat: float
    lon: float
    alt: Optional[float] = None  # Altitude in meters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_geojson_coords(self) -> List[float]:
        """Convert to GeoJSON coordinate array [lon, lat] or [lon, lat, alt]."""
        if self.alt is not None:
            return [self.lon, self.lat, self.alt]
        return [self.lon, self.lat]


@dataclass
class TrackedObject:
    """Represents a tracked object or asset."""
    id: str
    name: str
    location: GeoLocation
    criticality: CriticalityLevel
    vulnerability_score: float  # 0.0 to 1.0
    asset_value: float  # Arbitrary units
    dependencies: List[str] = field(default_factory=list)  # IDs of dependent objects
    tenant_id: str = "default_tenant"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON Point feature."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": self.location.to_geojson_coords()
            },
            "properties": {
                "entity_type": EntityType.OBJECT.value,
                "id": self.id,
                "name": self.name,
                "criticality": self.criticality.name,
                "criticality_value": self.criticality.value,
                "vulnerability_score": self.vulnerability_score,
                "asset_value": self.asset_value,
                "vulnerability_score": self.vulnerability_score,
                "asset_value": self.asset_value,
                "dependencies": self.dependencies,
                "tenant_id": self.tenant_id,
                **self.metadata
            }
        }


@dataclass
class Personnel:
    """Represents a person (first responder, operator, etc.)."""
    id: str
    name: str
    role: str
    location: GeoLocation
    criticality: CriticalityLevel  # Based on role importance
    on_duty: bool
    safety_clearances: List[str] = field(default_factory=list)  # e.g., ["radiation", "chemical"]
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    tenant_id: str = "default_tenant"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON Point feature."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": self.location.to_geojson_coords()
            },
            "properties": {
                "entity_type": EntityType.PERSONNEL.value,
                "id": self.id,
                "name": self.name,
                "role": self.role,
                "criticality": self.criticality.name,
                "criticality_value": self.criticality.value,
                "on_duty": self.on_duty,
                "safety_clearances": self.safety_clearances,
                "contact_phone": self.contact_phone,
                "contact_email": self.contact_email,
                "tenant_id": self.tenant_id,
                **self.metadata
            }
        }


@dataclass
class AreaOfInterest:
    """Represents an area or zone."""
    id: str
    name: str
    polygon_coords: List[List[float]]  # GeoJSON polygon coordinates [[lon, lat], ...]
    population_density: int  # People per sq km
    historical_incident_count: int
    strategic_importance: CriticalityLevel
    available_resources: List[str] = field(default_factory=list)  # e.g., ["hospital", "shelter"]
    tenant_id: str = "default_tenant"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON Polygon feature."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [self.polygon_coords]
            },
            "properties": {
                "entity_type": EntityType.AREA.value,
                "id": self.id,
                "name": self.name,
                "population_density": self.population_density,
                "historical_incident_count": self.historical_incident_count,
                "strategic_importance": self.strategic_importance.name,
                "strategic_importance_value": self.strategic_importance.value,
                "strategic_importance_value": self.strategic_importance.value,
                "available_resources": self.available_resources,
                "tenant_id": self.tenant_id,
                **self.metadata
            }
        }


@dataclass
class ThreatEvent:
    """Represents a threat event."""
    id: str
    timestamp: datetime
    threat_type: ThreatType
    location: GeoLocation
    magnitude: float  # Threat-specific magnitude (0.0 to 10.0)
    source: str  # e.g., "sensor_network", "manual_report"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "threat_type": self.threat_type.value,
            "location": self.location.to_dict(),
            "magnitude": self.magnitude,
            "source": self.source,
            "metadata": self.metadata
        }


@dataclass
class IncidentRecord:
    """Record of a triggered incident."""
    id: str
    event_id: str
    timestamp: datetime
    threat_type: ThreatType
    location: GeoLocation
    magnitude: float
    risk_score: float
    escalation_level: EscalationLevel
    affected_entities: List[str] = field(default_factory=list)  # Entity IDs
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)
    response_outcome: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "threat_type": self.threat_type.value,
            "location": self.location.to_dict(),
            "magnitude": self.magnitude,
            "risk_score": self.risk_score,
            "escalation_level": self.escalation_level.value,
            "affected_entities": self.affected_entities,
            "notifications_sent": self.notifications_sent,
            "response_outcome": self.response_outcome,
            "metadata": self.metadata
        }


class EntityRepository:
    """Repository for storing and querying entities."""
    
    def __init__(self):
        self.objects: Dict[str, TrackedObject] = {}
        self.personnel: Dict[str, Personnel] = {}
        self.areas: Dict[str, AreaOfInterest] = {}
    
    def add_object(self, obj: TrackedObject) -> None:
        """Add a tracked object."""
        self.objects[obj.id] = obj
    
    def add_personnel(self, person: Personnel) -> None:
        """Add personnel."""
        self.personnel[person.id] = person
    
    def add_area(self, area: AreaOfInterest) -> None:
        """Add an area of interest."""
        self.areas[area.id] = area
    
    def get_all_geojson(self) -> Dict[str, Any]:
        """Export all entities as a GeoJSON FeatureCollection."""
        features = []
        
        for obj in self.objects.values():
            features.append(obj.to_geojson())
        
        for person in self.personnel.values():
            features.append(person.to_geojson())
        
        for area in self.areas.values():
            features.append(area.to_geojson())
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def get_tenant_geojson(self, tenant_id: str) -> Dict[str, Any]:
        """Export entities for a specific tenant as GeoJSON."""
        features = []
        
        for obj in self.objects.values():
            if obj.tenant_id == tenant_id:
                features.append(obj.to_geojson())
        
        for person in self.personnel.values():
            if person.tenant_id == tenant_id:
                features.append(person.to_geojson())
        
        for area in self.areas.values():
            if area.tenant_id == tenant_id:
                features.append(area.to_geojson())
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def save_to_file(self, filepath: str) -> None:
        """Save repository to a GeoJSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.get_all_geojson(), f, indent=2)
    
    def load_from_file(self, filepath: str) -> None:
        """Load repository from a GeoJSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for feature in data.get("features", []):
            props = feature["properties"]
            entity_type = props.get("entity_type")
            
            if entity_type == EntityType.OBJECT.value:
                coords = feature["geometry"]["coordinates"]
                loc = GeoLocation(lat=coords[1], lon=coords[0], alt=coords[2] if len(coords) > 2 else None)
                obj = TrackedObject(
                    id=props["id"],
                    name=props["name"],
                    location=loc,
                    criticality=CriticalityLevel[props["criticality"]],
                    vulnerability_score=props["vulnerability_score"],
                    asset_value=props["asset_value"],
                    dependencies=props.get("dependencies", []),
                    tenant_id=props.get("tenant_id", "default_tenant")
                )
                self.add_object(obj)
            
            elif entity_type == EntityType.PERSONNEL.value:
                coords = feature["geometry"]["coordinates"]
                loc = GeoLocation(lat=coords[1], lon=coords[0], alt=coords[2] if len(coords) > 2 else None)
                person = Personnel(
                    id=props["id"],
                    name=props["name"],
                    role=props["role"],
                    location=loc,
                    criticality=CriticalityLevel[props["criticality"]],
                    on_duty=props["on_duty"],
                    safety_clearances=props.get("safety_clearances", []),
                    contact_phone=props.get("contact_phone"),
                    contact_email=props.get("contact_email"),
                    tenant_id=props.get("tenant_id", "default_tenant")
                )
                self.add_personnel(person)
            
            elif entity_type == EntityType.AREA.value:
                area = AreaOfInterest(
                    id=props["id"],
                    name=props["name"],
                    polygon_coords=feature["geometry"]["coordinates"][0],
                    population_density=props["population_density"],
                    historical_incident_count=props["historical_incident_count"],
                    strategic_importance=CriticalityLevel[props["strategic_importance"]],
                    available_resources=props.get("available_resources", []),
                    tenant_id=props.get("tenant_id", "default_tenant")
                )
                self.add_area(area)
