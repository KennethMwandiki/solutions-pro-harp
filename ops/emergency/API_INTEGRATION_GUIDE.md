# Quick API Integration Guide - For Immediate Implementation

Run these scripts to configure real APIs for the emergency response system.

## 1. Twilio SMS/Voice Setup (15 minutes)

### Sign Up & Get Credentials
1. Go to https://www.twilio.com/try-twilio
2. Create account, verify phone
3. Get: Account SID, Auth Token, Twilio phone number

### Create Config File
```bash
# Create .env file
cat > ops/emergency/.env <<'EOF'
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890
EOF
```

### Update notifications.py
```python
# Add to top of ops/emergency/notifications.py
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

class TwilioSMSHandler:
    def __init__(self):
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')
    
    def send(self, recipient, message, metadata=None):
        msg = self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=recipient
        )
        return NotificationResult(
            success=True,
            notification_type=NotificationType.SMS,
            recipient=recipient,
            message=message,
            timestamp=datetime.now(),
            metadata={'twilio_sid': msg.sid}
        )

# Replace MockSMSHandler in NotificationDispatcher.__init__
# self.sms_handler = TwilioSMSHandler()
```

### Install Dependencies
```bash
pip install twilio python-dotenv
```

---

## 2. Slack Webhook Setup (10 minutes)

### Create Webhook
1. Go to https://api.slack.com/messaging/webhooks
2. Click "Create an app" → "From scratch"
3. Name: "ProHarp Emergency Alerts"
4. Activate Incoming Webhooks
5. Copy webhook URL

### Add to .env
```bash
echo 'SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/xxxx' >> ops/emergency/.env
```

### Update notifications.py
```python
import requests

class SlackHandler:
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    def send(self, channel, message, metadata=None):
        response = requests.post(self.webhook_url, json={
            'text': message,
            'channel': channel
        })
        return NotificationResult(
            success=response.status_code == 200,
            notification_type=NotificationType.CHATOPS,
            recipient=channel,
            message=message,
            timestamp=datetime.now()
        )

# Replace MockChatOpsHandler in NotificationDispatcher
# self.chatops_handler = SlackHandler()
```

---

## 3. Firebase Cloud Messaging Setup (20 minutes)

### Create Firebase Project
1. Go to https://console.firebase.google.com
2. Create project: "ProHarp Emergency"
3. Add app → Select Cloud Messaging
4. Download `service-account.json`
5. Move to `ops/emergency/firebase-service-account.json`

### Add to .env
```bash
echo 'FIREBASE_SERVICE_ACCOUNT_PATH=ops/emergency/firebase-service-account.json' >> ops/emergency/.env
```

### Update notifications.py
```python
import firebase_admin
from firebase_admin import credentials, messaging

class FCMPushHandler:
    def __init__(self):
        cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    
    def send(self, device_token, message_text, metadata=None):
        message = messaging.Message(
            notification=messaging.Notification(
                title='🚨 Emergency Alert',
                body=message_text
            ),
            token=device_token,
            data=metadata or {}
        )
        response = messaging.send(message)
        return NotificationResult(
            success=True,
            notification_type=NotificationType.PUSH,
            recipient=device_token,
            message=message_text,
            timestamp=datetime.now(),
            metadata={'fcm_message_id': response}
        )

# Replace MockPushHandler in NotificationDispatcher
# self.push_handler = FCMPushHandler()
```

### Install Dependencies
```bash
pip install firebase-admin
```

---

## 4. Azure Sentinel Integration (30 minutes)

### Create Sentinel Connector
```python
# ops/emergency/azure_sentinel_connector.py
import os
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient
from datetime import datetime, timedelta
from event_processor import EventProcessor
from sample_data import generate_sample_data
from data_models import ThreatEvent, ThreatType, GeoLocation

class SentinelConnector:
    def __init__(self, workspace_id):
        self.credential = DefaultAzureCredential()
        self.logs_client = LogsQueryClient(self.credential)
        self.workspace_id = workspace_id
        self.processor = EventProcessor()
        self.entity_repo = generate_sample_data()
    
    def poll_alerts(self):
        """Poll Sentinel for new high-confidence alerts."""
        query = """
        ProHarpAnomalies_CL
        | where Confidence > 0.7
        | where TimeGenerated > ago(5m)
        | project TimeGenerated, AnomalyType, Confidence, Lat, Lon, Magnitude=coalesce(Magnitude, 5.0)
        """
        
        response = self.logs_client.query_workspace(
            workspace_id=self.workspace_id,
            query=query,
            timespan=timedelta(minutes=5)
        )
        
        for row in response.tables[0].rows:
            # Convert Sentinel alert to ThreatEvent
            event = ThreatEvent(
                id=f"sentinel-{row[0]}",
                timestamp=row[0],
                threat_type=ThreatType(row[1].lower()),
                location=GeoLocation(lat=row[3], lon=row[4]),
                magnitude=row[5],
                source="azure_sentinel"
            )
            
            # Process through emergency system
            self.processor.process_event(event, self.entity_repo)

if __name__ == "__main__":
    workspace_id = os.getenv('SENTINEL_WORKSPACE_ID')
    connector = SentinelConnector(workspace_id)
    
    # Run continuously
    import time
    while True:
        connector.poll_alerts()
        time.sleep(30)  # Poll every 30 seconds
```

### Add to .env
```bash
echo 'SENTINEL_WORKSPACE_ID=your-workspace-guid' >> ops/emergency/.env
```

### Install Dependencies
```bash
pip install azure-identity azure-monitor-query
```

---

## 5. Deploy to Azure Functions (45 minutes)

### Create Function App
```bash
# Install Azure Functions Core Tools
# https://learn.microsoft.com/azure/azure-functions/functions-run-local

# Create function app
cd ops/emergency
func init emergency_functions --python
cd emergency_functions

# Create timer-triggered function
func new --name SentinelPoller --template "Timer trigger"
```

### Copy Emergency System Files
```bash
cp ../geo_utils.py .
cp ../data_models.py .
cp ../rule_engine.py .
cp ../notifications.py .
cp ../event_processor.py .
cp ../azure_sentinel_connector.py .
cp ../config.yaml .
cp ../.env local.settings.json  # Convert to JSON format
```

### Update function_app.py
```python
import azure.functions as func
from azure_sentinel_connector import SentinelConnector
import os

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */1 * * * *", arg_name="timer")
def sentinel_poller(timer: func.TimerRequest) -> None:
    workspace_id = os.getenv('SENTINEL_WORKSPACE_ID')
    connector = SentinelConnector(workspace_id)
    connector.poll_alerts()
```

### Deploy to Azure
```bash
# Create Function App in Azure
az functionapp create \
  --resource-group proharp-prod \
  --name proharp-emergency \
  --storage-account proharpstore \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11

# Deploy function
func azure functionapp publish proharp-emergency

# Set environment variables
az functionapp config appsettings set \
  --name proharp-emergency \
  --resource-group proharp-prod \
  --settings @local.settings.json
```

---

## 6. Test End-to-End (15 minutes)

### Test Script
```python
# ops/emergency/test_real_apis.py
from notifications import NotificationDispatcher
from data_models import ThreatEvent, ThreatType, GeoLocation
from datetime import datetime
import uuid

# Test notification
dispatcher = NotificationDispatcher()

# Create test evaluation result
test_event = {
    "event_id": str(uuid.uuid4()),
    "threat_type": "fire",
    "magnitude": 7.5,
    "location": {"lat": 40.7128, "lon": -74.0060},
    "escalation_level": "high",
    "max_risk_score": 8.2,
    "affected_entities": [
        {"id": "test-1", "name": "Test Entity", "type": "object", "risk_score": 8.2}
    ],
    "contacts_to_notify": ["local", "regional"],
    "contact_numbers": ["+15551234567"]  # Your test phone
}

# Test SMS
sms_results = dispatcher.dispatch_sms(test_event, ["+15551234567"])
print(f"SMS: {sms_results[0].success}")

# Test Slack
slack_result = dispatcher.dispatch_chatops(test_event, "#emergency-test")
print(f"Slack: {slack_result.success}")

# Test Push (if you have device token)
# push_results = dispatcher.dispatch_push(test_event, ["device-token-here"])
# print(f"Push: {push_results[0].success}")
```

Run test:
```bash
python ops/emergency/test_real_apis.py
```

---

## Summary - Implementation Checklist

- [ ] Twilio account created, credentials in `.env`
- [ ] Slack webhook created, URL in `.env`
- [ ] Firebase project created, service account downloaded
- [ ] Azure Sentinel workspace ID added to `.env`
- [ ] Python dependencies installed (`pip install twilio python-dotenv firebase-admin azure-identity azure-monitor-query`)
- [ ] `notifications.py` updated with real handlers
- [ ] `azure_sentinel_connector.py` created
- [ ] Test script run successfully
- [ ] Azure Function deployed (optional but recommended)

**Total Time: 90-120 minutes for full integration**
