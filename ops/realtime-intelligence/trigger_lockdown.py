import os
import uuid
import datetime
import requests
import json

# Configuration (Set these env vars or replace values)
TOPIC_ENDPOINT = os.environ.get("EVENT_GRID_ENDPOINT", "REPLACE_WITH_TOPIC_ENDPOINT")
TOPIC_KEY = os.environ.get("EVENT_GRID_KEY", "REPLACE_WITH_TOPIC_KEY")

def send_anomaly_event():
    if "REPLACE" in TOPIC_ENDPOINT:
        print("[ERROR] Please set EVENT_GRID_ENDPOINT and EVENT_GRID_KEY environment variables.")
        print("Run: az eventgrid topic show --name proharp-prod-events --resource-group proharp-prod-rg --query endpoint --output tsv")
        print("Run: az eventgrid topic key list --name proharp-prod-events --resource-group proharp-prod-rg --query key1 --output tsv")
        return

    event_id = str(uuid.uuid4())
    event_time = datetime.datetime.utcnow().isoformat() + "Z"
    
    payload = [{
        "id": event_id,
        "eventType": "Orbital.Anomaly.Detected",
        "subject": "Satellite/VTH-101",
        "eventTime": event_time,
        "data": {
            "severity": "critical",
            "confidence": 0.95,
            "message": "Orbital deviation detected. Immediate lockdown recommended.",
            "coordinates": { "lat": 28.5, "lon": -80.6 }
        },
        "dataVersion": "1.0"
    }]
    
    headers = {
        "aeg-sas-key": TOPIC_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(TOPIC_ENDPOINT, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(f"[OK] Event {event_id} sent successfully!")
            print("Check your Logic App run history for the 'Lockdown' trigger.")
        else:
            print(f"[ERROR] Failed to send event. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    send_anomaly_event()
