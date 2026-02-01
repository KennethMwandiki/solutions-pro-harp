"""
Test scenarios for the emergency response system.

This module provides various threat scenarios for testing the system.
"""

import uuid
from datetime import datetime
from typing import List

from ops.emergency.data_models import ThreatEvent, ThreatType, GeoLocation


def generate_test_scenarios() -> List[ThreatEvent]:
    """
    Generate a variety of test threat scenarios.
    
    Returns:
        List of threat events
    """
    scenarios = []
    
    # Scenario 1: Low-magnitude fire near power station
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.FIRE,
        location=GeoLocation(40.7130, -74.0065),  # Very close to power station
        magnitude=2.5,
        source="sensor_network",
        metadata={"detected_by": "smoke_detector_grid", "confidence": 0.9}
    ))
    
    # Scenario 2: High-magnitude medical emergency at hospital
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.MEDICAL,
        location=GeoLocation(40.7250, -74.0050),  # At hospital
        magnitude=8.0,
        source="manual_report",
        metadata={"type": "mass_casualty", "patients": 25}
    ))
    
    # Scenario 3: Security threat in downtown
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.SECURITY,
        location=GeoLocation(40.7140, -74.0070),
        magnitude=6.5,
        source="law_enforcement",
        metadata={"type": "active_threat", "armed": True}
    ))
    
    # Scenario 4: Radiation detection near data center
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.RADIATION,
        location=GeoLocation(40.7105, -74.0085),
        magnitude=3.2,  # Sv
        source="radiation_monitor",
        metadata={"isotope": "Cs-137", "background_level": 0.1}
    ))
    
    # Scenario 5: Seismic event affecting wide area
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.SEISMIC,
        location=GeoLocation(40.7150, -74.0100),
        magnitude=5.8,  # Richter
        source="usgs",
        metadata={"depth_km": 10, "aftershocks_expected": True}
    ))
    
    # Scenario 6: Chemical spill in industrial area
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.CHEMICAL,
        location=GeoLocation(40.7000, -74.0100),  # Industrial zone
        magnitude=7.5,
        source="facility_alarm",
        metadata={"chemical": "chlorine", "volume_liters": 500, "wind_direction": "NE"}
    ))
    
    # Scenario 7: Severe weather approaching residential area
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.WEATHER,
        location=GeoLocation(40.7320, -74.0180),
        magnitude=8.5,
        source="nws",
        metadata={"type": "tornado", "category": "EF3", "speed_mph": 45}
    ))
    
    # Scenario 8: Low-priority event outside main perimeter (should be filtered)
    scenarios.append(ThreatEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        threat_type=ThreatType.FIRE,
        location=GeoLocation(40.8000, -74.1000),  # Far away
        magnitude=1.5,
        source="sensor_network",
        metadata={"type": "controlled_burn"}
    ))
    
    return scenarios


def run_scenario_tests():
    """Run all test scenarios through the event processor."""
    from ops.emergency.sample_data import generate_sample_data
    from ops.emergency.event_processor import EventProcessor
    from ops.emergency.geo_utils import PerimeterGenerator
    from ops.emergency.data_models import GeoLocation, ThreatEvent # Ensure shared definitions
    
    print("=" * 70)
    print("🧪 RUNNING EMERGENCY RESPONSE SYSTEM TEST SCENARIOS")
    print("=" * 70)
    
    # Generate sample entities
    repo = generate_sample_data()
    print(f"\n📦 Loaded {len(repo.objects)} objects, {len(repo.personnel)} personnel, {len(repo.areas)} areas")
    
    # Create active perimeter (10 km radius around downtown)
    perimeter_feature = PerimeterGenerator.from_single_point(40.7128, -74.0060, 10)
    active_perimeter = perimeter_feature["geometry"]["coordinates"][0]
    print(f"🔲 Active perimeter: {len(active_perimeter)} points, radius ~10 km")
    
    # Initialize event processor
    processor = EventProcessor()
    
    # Generate test scenarios
    scenarios = generate_test_scenarios()
    print(f"\n🎭 Generated {len(scenarios)} test scenarios\n")
    
    # Process each scenario
    incidents_created = 0
    for i, event in enumerate(scenarios, 1):
        print(f"\n{'─' * 70}")
        print(f"Scenario {i}: {event.threat_type.value.upper()} (magnitude: {event.magnitude})")
        print(f"Location: {event.location.lat:.4f}, {event.location.lon:.4f}")
        print(f"Source: {event.source}")
        
        incident = processor.process_event(event, repo, active_perimeter)
        
        if incident:
            incidents_created += 1
            print(f"✅ INCIDENT CREATED")
            print(f"   ID: {incident.id}")
            print(f"   Escalation: {incident.escalation_level.value.upper()}")
            print(f"   Risk Score: {incident.risk_score:.2f}")
            print(f"   Affected Entities: {len(incident.affected_entities)}")
            print(f"   Notifications Sent: {sum(len(n['results']) for n in incident.notifications_sent)}")
        else:
            print(f"⏭️  No incident triggered (filtered or rate-limited)")
    
    # Print summary
    print(f"\n{'=' * 70}")
    print(f"📊 TEST SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total Scenarios: {len(scenarios)}")
    print(f"Incidents Created: {incidents_created}")
    print(f"Filtered/Rate-Limited: {len(scenarios) - incidents_created}")
    
    # Get statistics
    stats = processor.get_statistics()
    print(f"\n📈 INCIDENT STATISTICS:")
    print(f"   Total Incidents: {stats['total_incidents']}")
    print(f"   Escalation Breakdown: {stats['escalation_breakdown']}")
    print(f"   Threat Type Breakdown: {stats['threat_type_breakdown']}")
    
    print(f"\n✅ All tests completed. Check logs/ directory for detailed output.")


if __name__ == "__main__":
    run_scenario_tests()
