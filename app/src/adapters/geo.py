# SPDX-License-Identifier: MIT
from typing import Dict, Optional

def embed_geo(frame_meta: Dict, facility_id: Optional[str] = None) -> Dict:
    geo = {
        "latitude": frame_meta.get("latitude"),
        "longitude": frame_meta.get("longitude"),
        "altitude": frame_meta.get("altitude"),
        "orbitId": frame_meta.get("orbitId"),
    }
    if facility_id:
        geo["facility_id"] = facility_id
    return geo
