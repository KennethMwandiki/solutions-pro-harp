import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path to allow importing ops modules
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

try:
    from ops.emergency.event_processor import EventProcessor
except ImportError as e:
    st.error(f"Failed to import Pro-Harp modules: {e}")
    st.stop()

st.set_page_config(
    page_title="Pro-Harp Operations",
    page_icon="🛰️",
    layout="wide"
)

# --- Multi-tenancy Context ---
with st.sidebar:
    st.header("🏢 Context")
    selected_tenant = st.selectbox(
        "Tenant ID",
        options=["tenant-city-one", "tenant-b", "default_tenant"],
        index=0
    )
    st.divider()
    
    # Auto-refresh config
    enable_refresh = st.toggle("Live Updates", value=True)
    refresh_rate = st.slider("Refresh Rate (s)", 5, 60, 10)

st.title("🛰️ Pro-Harp Operational Dashboard")
st.caption(f"Viewing Context: **{selected_tenant}** | Mode: **Real-time** {'✅' if enable_refresh else '⏸️'}")

st.markdown("""
Welcome to the Pro-Harp Operations Center. This dashboard provides tools for:
- **Entity Management**: Managing geospatial entities (Objects, Personnel, Areas)
- **Perimeter Control**: Defining and visualizing security perimeters
- **Incident Intelligence**: Monitoring real-time incidents and orbital threats
""")

# Quick Stats with Auto-Refresh
@st.fragment(run_every=refresh_rate if enable_refresh else None)
def render_live_stats():
    try:
        # Point to the correct config path relative to project root
        config_path = str(project_root / "ops/emergency/config.yaml")
        log_dir = str(project_root / "logs")
        
        # Initialize processor just to read stats
        processor = EventProcessor(config_path=config_path, log_dir=log_dir)
        stats = processor.get_statistics()
        
        # In a real impl, we would filter stats by tenant here
        # For now, we show global stats but simulate tenant view
        
    except Exception as e:
        st.warning(f"Could not load statistics: {e}")
        stats = {}

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Recorded Incidents", stats.get("total_incidents", 0))

    with col2:
        high_sev = stats.get("escalation_breakdown", {}).get("high", 0)
        st.metric("High Severity Alerts", high_sev)

    with col3:
        st.metric("System Status", "ONLINE", delta="Active")

    st.markdown("---")
    st.subheader("Recent Activity Stream")

    if "recent_incidents" in stats and stats["recent_incidents"]:
        # Flatten for display
        display_data = []
        for inc in stats["recent_incidents"]:
            display_data.append({
                "Time": inc.get("timestamp"),
                "Threat": inc.get("threat_type"),
                "Magnitude": inc.get("magnitude"),
                "Escalation": inc.get("escalation_level"),
                "Affected": len(inc.get("affected_entities", []))
            })
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("No recent incidents logged in the system.")

render_live_stats()
