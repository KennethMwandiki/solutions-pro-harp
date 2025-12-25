import streamlit as st
import json
import pandas as pd
from pathlib import Path
import sys
import uuid

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

st.set_page_config(page_title="Entity Management", page_icon="👥", layout="wide")

st.title("👥 Entity Management")

# Data Directory
DATA_DIR = project_root / "ops/emergency/data"
OBJECTS_FILE = DATA_DIR / "objects.geojson"
PERSONNEL_FILE = DATA_DIR / "personnel.geojson"
AREAS_FILE = DATA_DIR / "areas.geojson"

def load_geojson(filepath):
    if not filepath.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(filepath, "r") as f:
        return json.load(f)

def save_geojson(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def features_to_df(features, props_to_cols):
    rows = []
    for f in features:
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [])
        
        row = {k: props.get(k) for k in props_to_cols}
        row["id"] = props.get("id")
        
        # Handle coordinates display
        if geom.get("type") == "Point":
            row["lon"] = coords[0]
            row["lat"] = coords[1]
        elif geom.get("type") == "Polygon":
            # Just show centroid or first point for simplicity in table
            if coords:
                row["lon"] = coords[0][0][0]
                row["lat"] = coords[0][0][1]
        
        rows.append(row)
    return pd.DataFrame(rows)

tab_obj, tab_pers, tab_area = st.tabs(["🏗️ Objects", "🧑‍🚒 Personnel", "🏘️ Areas"])

# --- OBJECTS ---
with tab_obj:
    st.subheader("Critical Infrastructure Objects")
    obj_data = load_geojson(OBJECTS_FILE)
    
    if obj_data["features"]:
        df_obj = features_to_df(
            obj_data["features"], 
            ["name", "criticality", "vulnerability_score", "asset_value"]
        )
        st.dataframe(df_obj, use_container_width=True)
    else:
        st.info("No objects defined.")
    
    with st.expander("➕ Add New Object"):
        with st.form("new_object"):
            new_name = st.text_input("Name")
            col_a, col_b = st.columns(2)
            with col_a:
                new_lat = st.number_input("Latitude", value=40.7128, format="%.4f")
                new_crit = st.selectbox("Criticality", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], key="obj_crit")
            with col_b:
                new_lon = st.number_input("Longitude", value=-74.0060, format="%.4f")
                new_vuln = st.slider("Vulnerability Score", 0.0, 1.0, 0.5)
            
            submitted = st.form_submit_button("Create Object")
            if submitted:
                new_id = f"obj-{uuid.uuid4().hex[:8]}"
                new_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [new_lon, new_lat]
                    },
                    "properties": {
                        "entity_type": "object",
                        "id": new_id,
                        "name": new_name,
                        "criticality": new_crit,
                        "vulnerability_score": new_vuln
                    }
                }
                obj_data["features"].append(new_feature)
                save_geojson(OBJECTS_FILE, obj_data)
                st.success(f"Added {new_name}")
                st.rerun()

# --- PERSONNEL ---
with tab_pers:
    st.subheader("Emergency Personnel")
    pers_data = load_geojson(PERSONNEL_FILE)
    
    if pers_data["features"]:
        df_pers = features_to_df(
            pers_data["features"],
            ["name", "role", "criticality", "on_duty", "contact_phone"]
        )
        st.dataframe(df_pers, use_container_width=True)
    
    with st.expander("➕ Add Personnel"):
        with st.form("new_person"):
            p_name = st.text_input("Name")
            p_role = st.text_input("Role")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_lat = st.number_input("Latitude", value=40.7128, format="%.4f", key="p_lat")
                p_on_duty = st.checkbox("On Duty", value=True)
            with col_p2:
                p_lon = st.number_input("Longitude", value=-74.0060, format="%.4f", key="p_lon")
                p_crit = st.selectbox("Criticality", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], key="p_crit")
            
            p_phone = st.text_input("Phone")
            
            p_submitted = st.form_submit_button("Add Personnel")
            if p_submitted:
                new_id = f"pers-{uuid.uuid4().hex[:8]}"
                new_feature = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [p_lon, p_lat]},
                    "properties": {
                        "entity_type": "personnel",
                        "id": new_id,
                        "name": p_name,
                        "role": p_role,
                        "criticality": p_crit,
                        "on_duty": p_on_duty,
                        "contact_phone": p_phone
                    }
                }
                pers_data["features"].append(new_feature)
                save_geojson(PERSONNEL_FILE, pers_data)
                st.success(f"Added {p_name}")
                st.rerun()

# --- AREAS ---
with tab_area:
    st.subheader("Areas of Interest")
    st.info("To edit areas, use the Perimeter Map tool to draw polygons interactively.")
    area_data = load_geojson(AREAS_FILE)
    
    if area_data["features"]:
        df_area = features_to_df(
            area_data["features"],
            ["name", "strategic_importance", "population_density"]
        )
        st.dataframe(df_area, use_container_width=True)
