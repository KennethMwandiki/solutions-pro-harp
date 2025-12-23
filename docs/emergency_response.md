# Emergency Response System Module

## Overview
Provides perimeter-based threat detection, risk scoring, and automated emergency response capabilities.

## Components
- Geospatial utilities (radial perimeters, convex hulls, point-in-polygon)
- Entity management (objects, personnel, areas)
- Rule engine with risk scoring
- Notification dispatcher (mock handlers for SMS, voice, push, ChatOps)
- Incident logging and audit trail

## Quick Start
```bash
# Generate sample data
python ops/emergency/sample_data.py

# Run test scenarios
python ops/emergency/test_scenarios.py
```

## Integration Points
- **Azure Sentinel**: Ingest threat events from Sentinel alerts
- **Logic Apps**: Trigger notifications via Azure Logic Apps
- **Pro-Harp Dashboard**: Visualize incidents and perimeters
- **Real-time Telemetry**: Connect to sensor networks and IoT devices

See `ops/emergency/README.md` for detailed documentation.
