import jwt

secret = "this-is-a-very-secure-secret-for-local-testing-only-12345"
payload = {
    "topic": "proharp/anomalies",
    "alerts": [
        {
            "timestamp": 1678886400,
            "anomaly_type": "person",
            "confidence": 0.95,
            "bbox": [10, 10, 100, 100],
            "geo": {
                "latitude": 47.6062,
                "longitude": -122.3321,
                "altitude": 100,
                "orbitId": "ORBIT-123",
                "facility_id": "FAC-001",
                "telemetry_source": "auto"
            }
        }
    ]
}

token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
