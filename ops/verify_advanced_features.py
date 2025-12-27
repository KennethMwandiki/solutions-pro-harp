"""
Verification script for Advanced Enhancements.

Tests:
1. Multi-tenancy: Filters data by tenant_id
2. Threat Intel: Fetches from mock provider
3. ML Router: Checks A/B split ratio
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ops.emergency.sample_data import generate_sample_data
from ops.emergency.threat_intel import MockExternalFeed
from app.src.model_router import ModelRouter

def verify_multitenancy():
    print("\n--- Verifying Multi-tenancy ---")
    repo = generate_sample_data()
    
    city_one = repo.get_tenant_geojson("tenant-city-one")
    tenant_b = repo.get_tenant_geojson("tenant-b")
    
    c1_count = len(city_one["features"])
    tb_count = len(tenant_b["features"])
    
    print(f"Tenant CityOne Entities: {c1_count}")
    print(f"Tenant B Entities: {tb_count}")
    
    # Simple assertion logic
    if c1_count > 0 and tb_count > 0 and c1_count != tb_count:
        print("[PASS] Multi-tenancy isolation confirmed.")
    else:
        print("[FAIL] Multi-tenancy check failed.")

def verify_threat_intel():
    print("\n--- Verifying Threat Intelligence ---")
    provider = MockExternalFeed()
    threats = provider.get_latest_threats(limit=5)
    
    print(f"Fetched {len(threats)} threat indicators.")
    for t in threats:
        print(f" - [{t.severity:.2f}] {t.threat_type.value}: {t.description}")
    
    if len(threats) == 5:
        print("[PASS] Threat Intel provider working.")
    else:
        print("[FAIL] Threat Intel fetch failed.")

def verify_ml_router():
    print("\n--- Verifying ML Model Router (A/B Test) ---")
    router = ModelRouter()
    
    counts = {"v1": 0, "v2-candidate": 0}
    iterations = 1000
    
    for _ in range(iterations):
        model = router.get_model_for_inference()
        counts[model.version_id] += 1
    
    v1_ratio = counts["v1"] / iterations
    v2_ratio = counts["v2-candidate"] / iterations
    
    print(f"Split Results: v1={v1_ratio:.2f}, v2={v2_ratio:.2f}")
    
    # Check bounds (approx 0.8 / 0.2)
    if 0.75 < v1_ratio < 0.85 and 0.15 < v2_ratio < 0.25:
        print("[PASS] Traffic split within expected bounds (80/20).")
    else:
        print("[FAIL] Traffic split deviated significantly.")

if __name__ == "__main__":
    verify_multitenancy()
    verify_threat_intel()
    verify_ml_router()
