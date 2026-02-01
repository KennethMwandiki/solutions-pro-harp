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

from ops.emergency.geo_utils import GeoUtils, PerimeterGenerator, Coordinate, GeocodingService

from ops.dashboard.auth import require_auth, get_current_user

@require_auth(role="Viewer")
def main():
    st.set_page_config(page_title="Perimeter Map", page_icon="🗺️", layout="wide")

    st.title("🗺️ Perimeter Definition Tool")

    # Data Paths
    DATA_DIR = project_root / "ops/emergency/data"
    OBJECTS_FILE = DATA_DIR / "objects.geojson"
    PERSONNEL_FILE = DATA_DIR / "personnel.geojson"
    AREAS_FILE = DATA_DIR / "areas.geojson"

    # --- User Info ---
    user = get_current_user()
    
    with st.sidebar:
        st.header("👤 Security Viewer")
        if user:
            st.write(f"**{user.get('displayName', 'Unknown')}**")
        st.divider()

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

    # --- Manual Perimeter Entry ---
    with st.sidebar:
        st.divider()
        st.header("📍 Manual Perimeter Entry")
        st.caption("Enter precise coordinates or location name for enterprise security.")
        
        # Location Lookup
        col_city, col_state = st.columns(2)
        m_city = col_city.text_input("City", placeholder="e.g. Austin")
        m_state = col_state.text_input("State", placeholder="e.g. TX")
        
        if st.button("Lookup Coordinates"):
            if m_city and m_state:
                query = f"{m_city}, {m_state}"
                coords = GeocodingService.geocode(query)
                if coords:
                    st.session_state["m_lat"] = coords.lat
                    st.session_state["m_lon"] = coords.lon
                    st.success(f"Found: {coords.lat:.5f}, {coords.lon:.5f}")
                else:
                    st.error("Location not found.")
            else:
                st.warning("Please enter both City and State.")

        m_lat = st.number_input("Latitude", value=st.session_state.get("m_lat", start_lat), format="%.5f", key="m_lat_input")
        m_lon = st.number_input("Longitude", value=st.session_state.get("m_lon", start_lon), format="%.5f", key="m_lon_input")
        
        # Auto-capture city/state if lat/lon changed manually
        if st.button("Identify Location"):
            addr = GeocodingService.reverse_geocode(m_lat, m_lon)
            if addr:
                st.info(f"Detected: {addr['city']}, {addr['state']}")
                # Optional: Update session state for next save
                st.session_state["detected_address"] = addr

        m_shape = st.selectbox("Shape", ["Radial", "Rectangular"])
        
        if m_shape == "Radial":
            m_radius = st.number_input("Radius (km)", value=0.5, step=0.1)
        else:
            col_w, col_h = st.columns(2)
            m_width = col_w.number_input("Width (km)", value=0.5, step=0.1)
            m_height = col_h.number_input("Height (km)", value=0.5, step=0.1)
            
        m_preview = st.button("Preview Manual Entry")
        
        if m_preview:
            # Refresh coordinates from components if needed (session state handles this)
            lat, lon = m_lat, m_lon
            
            # Fetch address if not already looked up
            props = {}
            if m_city and m_state:
                props = {"city": m_city, "state": m_state}
            else:
                addr = GeocodingService.reverse_geocode(lat, lon)
                if addr:
                    props = {"city": addr["city"], "state": addr["state"]}
            
            if m_shape == "Radial":
                manual_feat = PerimeterGenerator.from_single_point(lat, lon, m_radius, properties=props)
            else:
                manual_feat = PerimeterGenerator.from_rectangle(lat, lon, m_width, m_height, properties=props)
            
            # Add preview layer
            folium.GeoJson(
                manual_feat,
                name="Preview",
                style_function=lambda x: {
                    "fillColor": "yellow",
                    "color": "gold",
                    "weight": 3,
                    "dashArray": "5, 5",
                    "fillOpacity": 0.4
                }
            ).add_to(m)
            # Re-center map
            m.location = [lat, lon]
            st.success("Previewing manual entry. Use the 'Save' form below to persist.")
            st.session_state["pending_manual_geometry"] = manual_feat["geometry"]
            st.session_state["pending_manual_properties"] = manual_feat["properties"]

    st.markdown("### Interactive Operations Map")
    st.caption("Use the toolbar on the left to draw new perimeters. Click 'Save New Area' below after drawing.")

    output = st_folium(m, width=1200, height=600)

    # Handle New Drawings
    pending_geometry = None
    if output and output.get("last_active_drawing"):
        pending_geometry = output["last_active_drawing"]["geometry"]
    elif "pending_manual_geometry" in st.session_state:
        pending_geometry = st.session_state["pending_manual_geometry"]

    if pending_geometry:
        geometry = pending_geometry
        
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
                new_properties = {
                    "entity_type": "area",
                    "id": new_id,
                    "name": new_name,
                    "population_density": new_density,
                    "strategic_importance": new_crit,
                    "historical_incident_count": 0
                }
                
                # Merge manual properties (city/state) if available
                if "pending_manual_properties" in st.session_state:
                    new_properties.update(st.session_state["pending_manual_properties"])
                
                new_feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": new_properties
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
                    
                if "pending_manual_geometry" in st.session_state:
                    del st.session_state["pending_manual_geometry"]
                if "pending_manual_properties" in st.session_state:
                    del st.session_state["pending_manual_properties"]
                    
                st.success(f"Saved area '{new_name}'!")
                st.rerun()

if __name__ == "__main__":
    main()
