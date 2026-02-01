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
    from ops.dashboard.cosmos_service import CosmosService
except ImportError as e:
    st.error(f"Failed to import Pro-Harp modules: {e}")
    st.stop()

from ops.dashboard.auth import require_auth, get_current_user, is_authenticated

# Inject custom Pro-Harp branding CSS
def load_custom_css():
    css_path = current_dir / "assets" / "proharp_theme.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@require_auth(role="Viewer")
def main():
    load_custom_css()

    st.set_page_config(
        page_title="Pro-Harp Security Command",
        page_icon="🛡️",
        layout="wide"
    )

    # --- User Profile & Context ---
    user = get_current_user()
    
    with st.sidebar:
        st.header("👤 Security Operator")
        if user:
            st.write(f"**{user.get('displayName', 'Unknown')}**")
            st.caption(user.get('userPrincipalName', ''))
            
            if st.button("Logout"):
                from ops.dashboard.auth import AzureAuthenticator
                auth = AzureAuthenticator()
                auth.logout()
                st.rerun()
        st.divider()
        
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

    # Command header with modern styling
    st.markdown("""
    <div class="command-header">
        <h1>🛡️ Pro-Harp: Command Your Security Perimeter</h1>
        <p>Real-Time Threat Intelligence at Your Fingertips | Intelligent. Responsive. Always Vigilant.</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption(f"Viewing Context: **{selected_tenant}** | Mode: **Real-time** {'✅' if enable_refresh else '⏸️'}")

    st.markdown("""
    **Welcome to the Pro-Harp Security Command Center.** Empower your team with:
    - **Asset Intelligence**: Manage geospatial entities with precision
    - **Perimeter Command**: Define and visualize your security boundaries
    - **Threat Timeline**: Monitor real-time incidents and orbital anomalies
    """)

    # Quick Stats with Auto-Refresh
    @st.fragment(run_every=refresh_rate if enable_refresh else None)
    def render_live_stats():
        try:
            # Point to the correct config path relative to project root
            config_path = str(project_root / "ops/emergency/config.yaml")
            log_dir = str(project_root / "logs")
            
            # Initialize processor just to read stats (Legacy/Mock)
            processor = EventProcessor(config_path=config_path, log_dir=log_dir)
            stats = processor.get_statistics()
            
            # --- Real-Time Cosmos DB Integration ---
            cosmos_service = CosmosService()
            live_stats = cosmos_service.get_stats()
            recent_incidents = cosmos_service.get_recent_incidents(limit=10)
            
            if live_stats:
                 # Merge live stats over processor stats
                 stats["total_incidents"] = live_stats.get("total_incidents", 0)
                 # Adjust high sev count
                 if "escalation_breakdown" not in stats: stats["escalation_breakdown"] = {}
                 stats["escalation_breakdown"]["high"] = live_stats.get("high_severity", 0)

        except Exception as e:
            st.warning(f"Could not load statistics: {e}")
            stats = {}
            recent_incidents = []

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

        if recent_incidents:
            # Flatten for display using the Cosmos DB schema
            display_data = []
            for inc in recent_incidents:
                # Handle both raw Cosmos dicts and object scenarios if needed
                display_data.append({
                    "Time": inc.get("event_time", "Unknown"),
                    "Type": "Detection" if "data" in inc.get("raw_data", {}) else "Anomaly", # Infer type
                    "Message": inc.get("message", "No description"),
                    "Severity": inc.get("severity", "Unknown"),
                    "Confidence": f"{inc.get('confidence', 0)*100:.0f}%"
                })
            st.dataframe(display_data, use_container_width=True)
        elif "recent_incidents" in stats and stats["recent_incidents"]:
             # Fallback to legacy stats if Cosmos empty
            display_data = []
            for inc in stats["recent_incidents"]:
                display_data.append({
                    "Time": inc.get("timestamp"),
                    "Type": inc.get("threat_type"),
                    "Message": "Simulated Incident",
                    "Severity": inc.get("escalation_level"),
                    "Confidence": "N/A"
                })
            st.dataframe(display_data, use_container_width=True)
        else:
            st.info("No recent incidents logged in the system.")

    render_live_stats()

if __name__ == "__main__":
    main()
