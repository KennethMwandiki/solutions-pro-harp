import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import json
from pathlib import Path
import sys
import uuid

# Add project root path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

from ops.emergency.geo_utils import GeoUtils

st.set_page_config(page_title="Perimeter Map", page_icon="🗺️", layout="wide")

st.title("🗺️ Perimeter Definition Tool")

# Data Paths
DATA_DIR = project_root / "ops/emergency/data"
OBJECTS_FILE = DATA_DIR / "objects.geojson"
PERSONNEL_FILE = DATA_DIR / "personnel.geojson"
AREAS_FILE = DATA_DIR / "areas.geojson"

def load_data():
    data = {}
    for name, fpath in {"objects": OBJECTS_FILE, "personnel": PERSONNEL_FILE, "areas": AREAS_FILE}.items():
        if fpath.exists():
            with open(fpath, "r") as f:
                data[name] = json.load(f)
        else:
            data[name] = {"type": "FeatureCollection", "features": []}
    return data

data = load_data()

# Initialize Map
start_lat, start_lon = 40.7128, -74.0060  # Default to NYC
m = folium.Map(location=[start_lat, start_lon], zoom_start=13)

# Add Areas
folium.GeoJson(
    data["areas"],
    name="Areas",
    style_function=lambda x: {
        "fillColor": "orange",
        "color": "red",
        "weight": 2,
        "fillOpacity": 0.3
    },
    tooltip=folium.GeoJsonTooltip(fields=["name", "strategic_importance"])
).add_to(m)

# Add Objects
for feat in data["objects"]["features"]:
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]
    folium.Marker(
        [coords[1], coords[0]],
        popup=f"<b>{props['name']}</b><br>Type: Object<br>Crit: {props['criticality']}",
        icon=folium.Icon(color="blue", icon="building")
    ).add_to(m)

# Add Personnel
for feat in data["personnel"]["features"]:
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]
    icon_color = "green" if props.get("on_duty") else "gray"
    folium.Marker(
        [coords[1], coords[0]],
        popup=f"<b>{props['name']}</b><br>Role: {props['role']}<br>Status: {'On Duty' if props.get('on_duty') else 'Off Duty'}",
        icon=folium.Icon(color=icon_color, icon="user")
    ).add_to(m)

# Draw Control for new Areas
draw = Draw(
    export=True,
    position="topleft",
    draw_options={
        "polyline": False,
        "rectangle": True,
        "circle": True,
        "marker": False,
        "circlemarker": False,
        "polygon": True,
    },
)
draw.add_to(m)

st.markdown("### Interactive Operations Map")
st.caption("Use the toolbar on the left to draw new perimeters. Click 'Save New Area' below after drawing.")

output = st_folium(m, width=1200, height=600)

# Handle New Drawings
if output and output.get("last_active_drawing"):
    drawing = output["last_active_drawing"]
    geometry = drawing["geometry"]
    
    st.divider()
    st.subheader("💾 Save New Perimeter")
    
    with st.form("save_area"):
        new_name = st.text_input("Area Name", placeholder="e.g. Exclusion Zone Alpha")
        new_density = st.number_input("Population Density", value=0)
        new_crit = st.selectbox("Strategic Importance", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        submitted = st.form_submit_button("Save Area")
        if submitted and new_name:
            # Create new feature
            new_id = f"area-{uuid.uuid4().hex[:8]}"
            new_feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "entity_type": "area",
                    "id": new_id,
                    "name": new_name,
                    "population_density": new_density,
                    "strategic_importance": new_crit,
                    "historical_incident_count": 0
                }
            }
            
            # Load current areas, append, save
            if AREAS_FILE.exists():
                with open(AREAS_FILE, "r") as f:
                    current_areas = json.load(f)
            else:
                current_areas = {"type": "FeatureCollection", "features": []}
                
            current_areas["features"].append(new_feature)
            
            with open(AREAS_FILE, "w") as f:
                json.dump(current_areas, f, indent=2)
                
            st.success(f"Saved area '{new_name}'!")
            st.rerun()
