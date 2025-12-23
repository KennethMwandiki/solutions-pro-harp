# Emergency Response System

A comprehensive perimeter-based threat detection and prioritization system with geofencing, risk scoring, and automated emergency response.

## Features

- **Geospatial Utilities**: Radial perimeter generation, convex hull, point-in-polygon checks, distance calculations
- **Entity Management**: Track objects, personnel, and areas of interest with criticality levels
- **Rule Engine**: Risk scoring based on threat magnitude, entity criticality, vulnerability, and proximity
- **Escalation Matrix**: Configurable escalation levels (low/medium/high) per threat type
- **Notification System**: Mock handlers for SMS, voice, push, and ChatOps (ready for real API integration)
- **Circuit Breaker**: Rate limiting to prevent notification spam
- **Audit Logging**: JSONL-based incident and notification logs

## Quick Start

### 1. Install Dependencies

```bash
pip install pyyaml
```

### 2. Generate Sample Data

```bash
python ops/emergency/sample_data.py
```

This creates:
- `ops/emergency/data/sample_entities.geojson` - All entities combined
- `ops/emergency/data/objects.geojson` - Critical infrastructure objects
- `ops/emergency/data/personnel.geojson` - Personnel roster
- `ops/emergency/data/areas.geojson` - Areas of interest

### 3. Run Test Scenarios

```bash
python ops/emergency/test_scenarios.py
```

This processes 8 different threat scenarios through the complete pipeline and generates logs in `logs/`.

### 4. View Logs

- `logs/incidents.jsonl` - Incident records
- `logs/notifications.log` - All notifications
- `logs/sms_notifications.jsonl` - SMS notifications
- `logs/voice_notifications.jsonl` - Voice calls
- `logs/push_notifications.jsonl` - Push notifications
- `logs/chatops_notifications.jsonl` - ChatOps messages

## Architecture

```
ops/emergency/
├── geo_utils.py          # Geospatial utilities
├── data_models.py        # Entity schemas
├── config.yaml           # System configuration
├── rule_engine.py        # Risk scoring & escalation
├── notifications.py      # Notification handlers
├── event_processor.py    # Main pipeline
├── sample_data.py        # Sample data generator
└── test_scenarios.py     # Test scenarios
```

## Configuration

Edit `ops/emergency/config.yaml` to customize:

- **Thresholds**: Magnitude thresholds per threat type
- **Hotlines**: Emergency contact numbers
- **Escalation Matrix**: Which contacts to notify per level
- **Risk Scoring**: Weights for magnitude, criticality, vulnerability, proximity
- **Notifications**: Retry attempts, circuit breaker settings

## Usage Example

```python
from event_processor import EventProcessor
from sample_data import generate_sample_data
from data_models import ThreatEvent, ThreatType, GeoLocation
from datetime import datetime
import uuid

# Load entities
repo = generate_sample_data()

# Create processor
processor = EventProcessor()

# Create threat event
event = ThreatEvent(
    id=str(uuid.uuid4()),
    timestamp=datetime.now(),
    threat_type=ThreatType.FIRE,
    location=GeoLocation(40.7150, -74.0080),
    magnitude=6.5,
    source="sensor_network"
)

# Process event
incident = processor.process_event(event, repo)

if incident:
    print(f"Incident {incident.id} created")
    print(f"Escalation: {incident.escalation_level.value}")
    print(f"Risk Score: {incident.risk_score:.2f}")
```

## Integrating Real APIs

The notification handlers are mock implementations. To integrate real services:

### Twilio (SMS/Voice)

```python
# In notifications.py
from twilio.rest import Client

class TwilioSMSHandler(MockSMSHandler):
    def __init__(self, account_sid, auth_token, from_number, log_dir="logs"):
        super().__init__(log_dir)
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
    
    def send(self, recipient, message, metadata=None):
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=recipient
            )
            # Return NotificationResult...
        except Exception as e:
            # Handle error...
```

### Firebase Cloud Messaging (Push)

```python
import firebase_admin
from firebase_admin import messaging

class FCMPushHandler(MockPushHandler):
    def send(self, recipient, message, metadata=None):
        msg = messaging.Message(
            notification=messaging.Notification(
                title="Emergency Alert",
                body=message
            ),
            token=recipient
        )
        response = messaging.send(msg)
        # Return NotificationResult...
```

### Slack (ChatOps)

```python
import requests

class SlackHandler(MockChatOpsHandler):
    def __init__(self, webhook_url, log_dir="logs"):
        super().__init__(log_dir)
        self.webhook_url = webhook_url
    
    def send(self, recipient, message, metadata=None):
        response = requests.post(self.webhook_url, json={
            "text": message,
            "channel": recipient
        })
        # Return NotificationResult...
```

## Threat Types

- `FIRE` - Fire emergencies
- `MEDICAL` - Medical emergencies
- `SECURITY` - Security threats
- `RADIATION` - Radiation detection
- `SEISMIC` - Earthquakes
- `CHEMICAL` - Chemical spills
- `WEATHER` - Severe weather

## License

See LICENSE file.
