# Sentinel KQL Rules

This document stores Sentinel KQL rules for future reference.

## Geo-Fence Rules

### 1. Facility Geo-Fence Breach
This rule detects when an anomaly with high confidence is detected within a 500-meter radius of a facility.

```kql
ProHarpAnomalies_CL
| where Confidence >= 0.7
| extend Lat = todouble(Lat), Lon = todouble(Lon)
| extend FacilityLat = -0.289, FacilityLon = 37.893, FenceRadiusMeters = 500
| extend Distance = geo_distance_2points(Lat, Lon, FacilityLat, FacilityLon)
| where Distance < FenceRadiusMeters
| project Timestamp, AnomalyType, Confidence, Lat, Lon, Distance, FacilityId, TelemetrySource
```

### 2. Manual Override Audit
This rule audits manual telemetry overrides, counting them per facility per hour.

```kql
ProHarpAnomalies_CL
| where TelemetrySource == "manual"
| summarize Overrides = count() by FacilityId, bin(Timestamp, 1h)
```

### 3. Multi-Facility Intrusion
This rule detects if a "drone" anomaly is detected across multiple facilities within a 10-minute window.

```kql
ProHarpAnomalies_CL
| where AnomalyType == "drone" and Confidence > 0.8
| summarize Facilities = make_set(FacilityId) by bin(Timestamp, 10m)
| where array_length(Facilities) > 1
```
