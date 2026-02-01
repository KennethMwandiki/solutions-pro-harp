"""
Verification Script for Pro-Harp Real-Time Flow.
Publishes a mock 'Orbital Anomaly' event to the Event Grid Topic.
"""

import os
import datetime
import uuid
import requests
import json
import logging

# Configuration (In a real app, these would come from env vars or Key Vault)
# Using the values retrieved during deployment
TOPIC_ENDPOINT = "https://proharp-events.eastus-1.eventgrid.azure.net/api/events"
TOPIC_KEY = "REPLACE_WITH_YOUR_TOPIC_KEY"  # Placeholder for security

setup_logging = logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_test_event():
    logger.info(f"Sending test event to {TOPIC_ENDPOINT}")
    
    event_id = str(uuid.uuid4())
    event_time = datetime.datetime.utcnow().isoformat() + "Z"
    
    payload = [
        {
            "id": event_id,
            "eventType": "ProHarp.Orbital.AnomalyDetected",
            "subject": "/satellite/monitoring/sector-7",
            "eventTime": event_time,
            "data": {
                "anomaly_type": "trajectory_deviation",
                "severity": "high",
                "confidence": 0.98,
                "coordinates": {
                    "lat": 34.0522,
                    "lon": -118.2437,
                    "alt": 550000
                },
                "message": "Unidentified object deviation detected."
            },
            "dataVersion": "1.0"
        }
    ]
    
    headers = {
        "aeg-sas-key": TOPIC_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(TOPIC_ENDPOINT, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            logger.info("✅ Event sent successfully!")
            logger.info(f"Event ID: {event_id}")
            logger.info("Check Azure Function logs for processing confirmation.")
        else:
            logger.error(f"❌ Failed to send event. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"Exception sending event: {e}")

if __name__ == "__main__":
    send_test_event()
