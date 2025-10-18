README.md
# 🛰️ Pro‑Harp: Geo‑Intelligent Orbital Security Platform

Pro‑Harp is a modular orbital security solution built on the [Azure Orbital Space SDK](https://github.com/microsoft/azure-orbital-space-sdk). It enables real-time anomaly detection from space, geospatial threat correlation, and automated enterprise response for data center protection across diverse regions.

---
## 🚀 Capabilities

- **On-Orbit AI Inference**: Detects vehicles, drones, excavation equipment, floods, and surveillance patterns using ONNX Runtime.
- **Geo-Intelligence**: Supports auto-geocoding from satellite telemetry and manual lat/long input for flexible regional coverage.
- **Containerized Deployment**: Runs lightweight ML models in orbital containers using SDK runtime.
- **Ground Integration**: Ingests alerts via .NET APIs, correlates with Azure Sentinel, and triggers Logic Apps playbooks.
- **Forensics & Compliance**: Stores signed telemetry and imagery in immutable Azure Blob Storage with Purview lineage.

---

## ⚠️ Limitations

- **Latency**: Real-time detection may vary based on satellite pass frequency and downlink availability.
- **Coverage**: Detection accuracy depends on sensor resolution and orbital visibility.
- **Bandwidth Constraints**: Full imagery is not downlinked—only flagged anomalies are transmitted.
- **Model Scope**: Initial models tuned for perimeter threats; additional training required for new threat classes.

---

## 📦 Directory Structure

```
solutions/pro-harp/
├── app/                  # Orbital container (ONNX + Python)
│   ├── src/
│   ├── models/
│   ├── Dockerfile
│   ├── LICENSE
│   └── README.md
├── ground/               # Ground ingestion and SOC integration (.NET)
│   ├── ingest/
│   ├── sentinel/
│   └── logic-apps/
├── ops/                  # CI/CD, deployment, VTH tests
│   ├── ci/
│   └── deployment/
```

---

## 🔧 Operational Playbooks

### 1. Orbital Deployment
- Build container image using Dockerfile.
- Test with Virtual Test Harness (VTH) using synthetic perimeter scenarios.
- Push to Azure Container Registry (ACR).
- Deploy to satellite host via SDK runtime.

### 2. Ground Ingestion
- Receive anomaly payloads via .NET API.
- Enrich with Azure Maps geocoding (auto/manual).
- Normalize and ingest into Sentinel custom table.

### 3. SOC Correlation
- Use KQL rules to match anomalies with CCTV, IoT, and access logs.
- Trigger Logic Apps for automated response (lockdown, dispatch, counter-drone).

### 4. Forensics & Audit
- Store alerts and imagery in Blob Storage with WORM policies.
- Register lineage in Microsoft Purview for compliance.

---

## 🔗 Upstream SDK References

- [Azure Orbital Space SDK GitHub](https://github.com/microsoft/azure-orbital-space-sdk)
- [ONNX Runtime Samples](https://github.com/microsoft/azure-orbital-space-sdk/tree/main/samples/onnx)
- [Virtual Test Harness Docs](https://github.com/microsoft/azure-orbital-space-sdk/tree/main/docs/vth)
- [Container Runtime Guide](https://github.com/microsoft/azure-orbital-space-sdk/tree/main/docs/runtime)

---

## 📜 Licensing & Attribution

This project reuses components from the Azure Orbital Space SDK under the [MIT License](https://github.com/microsoft/azure-orbital-space-sdk/blob/main/LICENSE). All reused files include SPDX headers and attribution in source comments. See `LICENSE` and `NOTICE` for details.

---

## 🛡️ Security & Support

- Vulnerability disclosures: See `SECURITY.md`
- Contribution guidelines: See `CONTRIBUTING.md`
- Code of conduct: See `CODE_OF_CONDUCT.md`

---

```

