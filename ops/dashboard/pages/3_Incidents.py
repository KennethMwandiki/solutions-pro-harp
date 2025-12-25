import streamlit as st
import pandas as pd
import json
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Incident Intelligence", page_icon="🚨", layout="wide")

st.title("🚨 Incident Intelligence")

# Paths
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
LOG_FILE = project_root / "logs/incidents.jsonl"

@st.cache_data(ttl=10)  # fast refresh
def load_incidents():
    if not LOG_FILE.exists():
        return pd.DataFrame()
    
    data = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    if not data:
        return pd.DataFrame()
        
    df = pd.DataFrame(data)
    # Flatten nested fields if needed or handle simple cols
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

df = load_incidents()

if df.empty:
    st.info("No incident logs found.")
    st.stop()

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
    fig_type = px.pie(df, names="threat_type", title="Incidents by Threat Type", hole=0.4)
    st.plotly_chart(fig_type, use_container_width=True)

with c2:
    # Incidents over time
    # Group by hour or minute depending on density
    df_sorted = df.sort_values("timestamp")
    fig_time = px.scatter(df_sorted, x="timestamp", y="magnitude", color="escalation_level", 
                       title="Incident Timeline & Magnitude", hover_data=["threat_type"])
    st.plotly_chart(fig_time, use_container_width=True)

# Map View
st.subheader("Geospatial Distribution")
# df['location'] is a dict, need to extract lat/lon
if "location" in df.columns:
    df_map = df.copy()
    df_map["lat"] = df_map["location"].apply(lambda x: x.get("lat"))
    df_map["lon"] = df_map["location"].apply(lambda x: x.get("lon"))
    
    st.map(df_map, latitude="lat", longitude="lon", size="magnitude", color="#ff0000")

# Detail Table
st.subheader("Incident Log")
st.dataframe(
    df[["timestamp", "threat_type", "magnitude", "escalation_level", "risk_score", "id"]].sort_values("timestamp", ascending=False),
    use_container_width=True
)
