"""
Sample data generator for emergency response system testing.

This module creates realistic test data for objects, personnel, and areas.
"""

import json
from pathlib import Path

from ops.emergency.data_models import (
    TrackedObject, Personnel, AreaOfInterest, CriticalityLevel,
    GeoLocation, EntityRepository
)
from ops.emergency.geo_utils import PerimeterGenerator


def generate_sample_data() -> EntityRepository:
    """
    Generate sample data for testing.
    
    Returns:
        EntityRepository with sample entities
    """
    repo = EntityRepository()
    
    # ===== Critical Infrastructure Objects =====
    
    repo.add_object(TrackedObject(
        id="obj-power-001",
        name="Central Power Station",
        location=GeoLocation(40.7128, -74.0060),
        criticality=CriticalityLevel.CRITICAL,
        vulnerability_score=0.9,
        asset_value=5000000,
        dependencies=[],
        tenant_id="tenant-city-one",
        metadata={"type": "power_generation", "capacity_mw": 500}
    ))
    
    repo.add_object(TrackedObject(
        id="obj-water-001",
        name="Main Water Treatment Plant",
        location=GeoLocation(40.7200, -74.0100),
        criticality=CriticalityLevel.HIGH,
        vulnerability_score=0.7,
        asset_value=3000000,
        dependencies=["obj-power-001"],
        tenant_id="tenant-city-one",
        metadata={"type": "water_treatment", "capacity_mgd": 100}
    ))
    
    repo.add_object(TrackedObject(
        id="obj-comm-001",
        name="Emergency Communications Tower",
        location=GeoLocation(40.7080, -74.0150),
        criticality=CriticalityLevel.CRITICAL,
        vulnerability_score=0.6,
        asset_value=1000000,
        dependencies=["obj-power-001"],
        tenant_id="tenant-city-one",
        metadata={"type": "communications", "coverage_radius_km": 50}
    ))
    
    repo.add_object(TrackedObject(
        id="obj-hospital-001",
        name="Metro General Hospital",
        location=GeoLocation(40.7250, -74.0050),
        criticality=CriticalityLevel.CRITICAL,
        vulnerability_score=0.5,
        asset_value=10000000,
        dependencies=["obj-power-001", "obj-water-001"],
        tenant_id="tenant-city-one",
        metadata={"type": "hospital", "beds": 300, "trauma_center": True}
    ))
    
    repo.add_object(TrackedObject(
        id="obj-data-001",
        name="City Data Center",
        location=GeoLocation(40.7100, -74.0080),
        criticality=CriticalityLevel.HIGH,
        vulnerability_score=0.4,
        asset_value=2000000,
        dependencies=["obj-power-001", "obj-comm-001"],
        tenant_id="tenant-b",
        metadata={"type": "data_center", "uptime_sla": 99.99}
    ))
    
    # ===== Personnel =====
    
    repo.add_personnel(Personnel(
        id="pers-fire-chief",
        name="Chief Sarah Johnson",
        role="Fire Chief",
        location=GeoLocation(40.7150, -74.0070),
        criticality=CriticalityLevel.CRITICAL,
        on_duty=True,
        safety_clearances=["fire", "hazmat", "chemical"],
        contact_phone="+1-555-0101",
        contact_email="sjohnson@firecity.gov",
        tenant_id="tenant-city-one",
        metadata={"station": "Station 1", "years_service": 15}
    ))
    
    repo.add_personnel(Personnel(
        id="pers-emt-001",
        name="Dr. Michael Chen",
        role="Emergency Medical Director",
        location=GeoLocation(40.7250, -74.0050),
        criticality=CriticalityLevel.HIGH,
        on_duty=True,
        safety_clearances=["medical", "radiation", "chemical"],
        contact_phone="+1-555-0102",
        contact_email="mchen@metrohealth.org",
        tenant_id="tenant-city-one",
        metadata={"hospital": "Metro General", "specialty": "trauma"}
    ))
    
    repo.add_personnel(Personnel(
        id="pers-police-001",
        name="Captain Robert Martinez",
        role="Police Commander",
        location=GeoLocation(40.7180, -74.0090),
        criticality=CriticalityLevel.HIGH,
        on_duty=True,
        safety_clearances=["security"],
        contact_phone="+1-555-0103",
        contact_email="rmartinez@citypd.gov",
        tenant_id="tenant-city-one",
        metadata={"precinct": "Downtown", "swat_certified": True}
    ))
    
    repo.add_personnel(Personnel(
        id="pers-engineer-001",
        name="Emily Rodriguez",
        role="Infrastructure Engineer",
        location=GeoLocation(40.7128, -74.0060),
        criticality=CriticalityLevel.MEDIUM,
        on_duty=True,
        safety_clearances=["radiation", "chemical"],
        contact_phone="+1-555-0104",
        contact_email="erodriguez@cityworks.gov",
        tenant_id="tenant-city-one",
        metadata={"department": "Public Works", "specialization": "power_systems"}
    ))
    
    repo.add_personnel(Personnel(
        id="pers-responder-001",
        name="James Wilson",
        role="First Responder",
        location=GeoLocation(40.7210, -74.0110),
        criticality=CriticalityLevel.MEDIUM,
        on_duty=False,  # Off duty
        safety_clearances=["fire", "medical"],
        contact_phone="+1-555-0105",
        contact_email="jwilson@firecity.gov",
        tenant_id="tenant-b",
        metadata={"station": "Station 2"}
    ))
    
    # ===== Areas of Interest =====
    
    # Downtown district - high population density
    downtown_perimeter = PerimeterGenerator.from_single_point(40.7128, -74.0060, 2)
    repo.add_area(AreaOfInterest(
        id="area-downtown",
        name="Downtown Business District",
        polygon_coords=downtown_perimeter["geometry"]["coordinates"][0],
        population_density=15000,
        historical_incident_count=45,
        strategic_importance=CriticalityLevel.CRITICAL,
        available_resources=["hospital", "fire_station", "police_precinct", "shelter"],
        tenant_id="tenant-city-one",
        metadata={"zoning": "commercial", "evacuation_routes": 6}
    ))
    
    # Residential area
    residential_perimeter = PerimeterGenerator.from_single_point(40.7300, -74.0200, 1.5)
    repo.add_area(AreaOfInterest(
        id="area-residential",
        name="North Residential Zone",
        polygon_coords=residential_perimeter["geometry"]["coordinates"][0],
        population_density=8000,
        historical_incident_count=12,
        strategic_importance=CriticalityLevel.MEDIUM,
        available_resources=["fire_station", "shelter"],
        tenant_id="tenant-city-one",
        metadata={"zoning": "residential", "schools": 3}
    ))
    
    # Industrial zone
    industrial_coords = [
        (40.7050, -74.0200),
        (40.7050, -73.9950),
        (40.6950, -73.9950),
        (40.6950, -74.0200)
    ]
    industrial_perimeter = PerimeterGenerator.from_multiple_points(industrial_coords)
    repo.add_area(AreaOfInterest(
        id="area-industrial",
        name="South Industrial Park",
        polygon_coords=industrial_perimeter["geometry"]["coordinates"][0],
        population_density=500,
        historical_incident_count=28,
        strategic_importance=CriticalityLevel.HIGH,
        available_resources=["hazmat_team", "fire_station"],
        tenant_id="tenant-b",
        metadata={"zoning": "industrial", "hazardous_ materials": True}
    ))
    
    return repo


def save_sample_data(output_dir: str = "ops/emergency/data"):
    """
    Generate and save sample data to files.
    
    Args:
        output_dir: Directory to save data files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    repo = generate_sample_data()
    
    # Save as GeoJSON
    geojson_path = output_path / "sample_entities.geojson"
    repo.save_to_file(str(geojson_path))
    print(f"✅ Saved sample entities to {geojson_path}")
    
    # Save individual entity type files for easier inspection
    objects_data = {
        "type": "FeatureCollection",
        "features": [obj.to_geojson() for obj in repo.objects.values()]
    }
    with open(output_path / "objects.geojson", 'w') as f:
        json.dump(objects_data, f, indent=2)
    
    personnel_data = {
        "type": "FeatureCollection",
        "features": [person.to_geojson() for person in repo.personnel.values()]
    }
    with open(output_path / "personnel.geojson", 'w') as f:
        json.dump(personnel_data, f, indent=2)
    
    areas_data = {
        "type": "FeatureCollection",
        "features": [area.to_geojson() for area in repo.areas.values()]
    }
    with open(output_path / "areas.geojson", 'w') as f:
        json.dump(areas_data, f, indent=2)
    
    print(f"✅ Saved {len(repo.objects)} objects")
    print(f"✅ Saved {len(repo.personnel)} personnel")
    print(f"✅ Saved {len(repo.areas)} areas")
    
    return repo


if __name__ == "__main__":
    save_sample_data()
