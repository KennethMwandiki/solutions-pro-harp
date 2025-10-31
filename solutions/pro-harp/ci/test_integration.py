# SPDX-License-Identifier: MIT
import requests, jwt, time, sys, os

def run():
    endpoint = f"http://localhost:{os.environ.get('INGEST_PORT', 8080)}/ingest"
    debug_endpoint = f"http://localhost:{os.environ.get('INGEST_PORT', 8080)}/debug/logs"
    secret = os.environ.get('ORBITAL_SECRET', 'test-secret-rotate-me')

    # Test 1: Auto telemetry
    print("Running test 1: Auto telemetry")
    payload_auto = {
      "topic": "proharp/anomalies",
      "count": 1,
      "alerts": [{
        "timestamp": int(time.time()),
        "anomaly_type": "drone",
        "confidence": 0.93,
        "bbox": [10,20,100,200],
        "geo": {
          "latitude": -0.289,
          "longitude": 37.893,
          "altitude": 550000,
          "orbitId": "CI-ORB",
          "facility_id": "CI-FAC-1",
          "telemetry_source": "auto",
          "manual_override": {"enabled": False, "latitude": None, "longitude": None, "reason": None}
        }
      }]
    }
    token_auto = jwt.encode(payload_auto, secret, algorithm="HS256")
    envelope_auto = {"payload": payload_auto, "signature": token_auto}
    r_auto = requests.post(endpoint, json=envelope_auto, timeout=10)
    print("Status", r_auto.status_code, r_auto.text)
    if r_auto.status_code != 200:
        raise SystemExit(2)
    print("OK")

    # Test 2: Manual override
    print("Running test 2: Manual override")
    payload_manual = {
      "topic": "proharp/anomalies",
      "count": 1,
      "alerts": [{
        "timestamp": int(time.time()),
        "anomaly_type": "excavation",
        "confidence": 0.98,
        "bbox": [150,250,200,300],
        "geo": {
          "latitude": -0.289,
          "longitude": 37.893,
          "altitude": 550000,
          "orbitId": "CI-ORB",
          "facility_id": "CI-FAC-1",
          "telemetry_source": "manual",
          "manual_override": {"enabled": True, "latitude": -0.290, "longitude": 37.900, "reason": "Operator override"}
        }
      }]
    }
    token_manual = jwt.encode(payload_manual, secret, algorithm="HS256")
    envelope_manual = {"payload": payload_manual, "signature": token_manual}
    r_manual = requests.post(endpoint, json=envelope_manual, timeout=10)
    print("Status", r_manual.status_code, r_manual.text)
    if r_manual.status_code != 200:
        raise SystemExit(3)
    print("OK")

    # Verification
    print("Verifying ingested records...")
    time.sleep(2) # give a moment for logs to process
    r_logs = requests.get(debug_endpoint, timeout=10)
    if r_logs.status_code != 200:
        print("Error fetching debug logs:", r_logs.status_code, r_logs.text)
        raise SystemExit(4)
    
    logs = r_logs.json()
    print(f"Retrieved {len(logs)} records from debug endpoint.")

    assert len(logs) >= 2, f"Expected at least 2 records, but got {len(logs)}"

    # Check auto telemetry record
    auto_record = next((r for r in logs if r['anomalyType'] == 'drone'), None)
    assert auto_record is not None, "Auto telemetry record not found"
    assert auto_record['telemetrySource'] == 'auto', f"Incorrect telemetry source: {auto_record['telemetrySource']}"
    assert auto_record['lat'] == -0.289, f"Incorrect latitude: {auto_record['lat']}"
    assert auto_record['manualLat'] is None, f"Manual latitude should be null: {auto_record['manualLat']}"
    print("Auto telemetry record verified.")

    # Check manual override record
    manual_record = next((r for r in logs if r['anomalyType'] == 'excavation'), None)
    assert manual_record is not None, "Manual override record not found"
    assert manual_record['telemetrySource'] == 'manual', f"Incorrect telemetry source: {manual_record['telemetrySource']}"
    assert manual_record['lat'] == -0.289, f"Incorrect auto latitude: {manual_record['lat']}"
    assert manual_record['manualLat'] == -0.290, f"Incorrect manual latitude: {manual_record['manualLat']}"
    assert manual_record['manualReason'] == "Operator override", f"Incorrect manual reason: {manual_record['manualReason']}"
    print("Manual override record verified.")

    print("All integration tests passed!")

if __name__ == '__main__':
    run()