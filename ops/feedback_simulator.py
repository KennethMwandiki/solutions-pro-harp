import json
import requests
import time
import os

LOG_FILE = "../ground/ingest/sentinel_output.log"
API_URL = "http://localhost:5000/feedback"

def simulate_feedback():
    print(f"Reading logs from {LOG_FILE}...")
    if not os.path.exists(LOG_FILE):
        print("Log file not found.")
        return

    with open(LOG_FILE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                alert = json.loads(line)
                alert_id = alert.get("Id")
                confidence = alert.get("Confidence", 0)
                
                # Logic: High confidence = True Positive, Low = False Positive (Simulated)
                is_tp = confidence > 0.9
                correct_label = alert.get("AnomalyType") if is_tp else "background"

                feedback = {
                    "AlertId": alert_id,
                    "IsTruePositive": is_tp,
                    "CorrectLabel": correct_label
                }

                print(f"Sending feedback for {alert_id}: {feedback}")
                try:
                    r = requests.post(API_URL, json=feedback)
                    print(f"Status: {r.status_code}")
                except Exception as e:
                    print(f"Failed to connect: {e}")
                
                time.sleep(0.5)

            except json.JSONDecodeError:
                continue

if __name__ == "__main__":
    simulate_feedback()
