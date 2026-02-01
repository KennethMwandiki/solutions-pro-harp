import streamlit as st
import pandas as pd
import json
import plotly.express as px
from pathlib import Path

from ops.dashboard.auth import require_auth, get_current_user

@require_auth(role="Viewer")
def main():
    st.set_page_config(page_title="Incident Intelligence", page_icon="🚨", layout="wide")

    st.title("🚨 Incident Intelligence")

    # Paths
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    LOG_FILE = project_root / "logs/incidents.jsonl"

    # --- User Info & Context ---
    user = get_current_user()
    
    with st.sidebar:
        st.header("👤 Security Viewer")
        if user:
            st.write(f"**{user.get('displayName', 'Unknown')}**")
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
        refresh_rate = st.slider("Refresh Rate (s)", 5, 60, 5)

    st.caption(f"Viewing Context: **{selected_tenant}** | Mode: **Real-time** {'✅' if enable_refresh else '⏸️'}")

    def load_incidents():
        if not LOG_FILE.exists():
            return pd.DataFrame()
        
        data = []
        # Read file - simplified for demo (in prod, use DB or smarter log reading)
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        # Filter by tenant if logic existed, for now just load all
                        # In real impl: if record.get('tenant_id') == selected_tenant:
                        data.append(record)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return pd.DataFrame()
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    @st.fragment(run_every=refresh_rate if enable_refresh else None)
    def render_live_incidents():
        df = load_incidents()

        if df.empty:
            st.info("No incident logs found.")
            return

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Incidents", len(df))
        with col2:
            st.metric("High Severity", len(df[df["escalation_level"] == "high"]))
        with col3:
            avg_risk = df["risk_score"].mean()
            st.metric("Avg Risk Score", f"{avg_risk:.2f}")
        with col4:
            last_inc = df["timestamp"].max().strftime("%H:%M:%S")
            st.metric("Last Incident", last_inc)

        # Charts
        st.subheader("Trends")
        c1, c2 = st.columns(2)

        with c1:
            # Incidents by Type
            if "threat_type" in df.columns:
                fig_type = px.pie(df, names="threat_type", title="Incidents by Threat Type", hole=0.4)
                st.plotly_chart(fig_type, use_container_width=True)

        with c2:
            # Incident Timeline
            if "magnitude" in df.columns:
                df_sorted = df.sort_values("timestamp")
                fig_time = px.scatter(df_sorted, x="timestamp", y="magnitude", color="escalation_level", 
                                title="Incident Timeline & Magnitude", hover_data=["threat_type"])
                st.plotly_chart(fig_time, use_container_width=True)

        # Map View
        st.subheader("Geospatial Distribution")
        if "location" in df.columns:
            df_map = df.copy()
            # Safe extraction of lat/lon
            df_map["lat"] = df_map["location"].apply(lambda x: x.get("lat") if isinstance(x, dict) else None)
            df_map["lon"] = df_map["location"].apply(lambda x: x.get("lon") if isinstance(x, dict) else None)
            df_map = df_map.dropna(subset=["lat", "lon"])
            
            if not df_map.empty:
                st.map(df_map, latitude="lat", longitude="lon", size="magnitude", color="#ff0000")
            else:
                st.info("No geospatial data available.")

        # Detail Table
        st.subheader("Incident Log")
        cols_to_show = ["timestamp", "threat_type", "magnitude", "escalation_level", "risk_score", "id"]
        # Filter only existing cols
        valid_cols = [c for c in cols_to_show if c in df.columns]
        
        st.dataframe(
            df[valid_cols].sort_values("timestamp", ascending=False),
            use_container_width=True
        )

    render_live_incidents()

if __name__ == "__main__":
    main()
