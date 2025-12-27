import streamlit as st
from datetime import datetime
import time

st.set_page_config(page_title="Pro-Harp Responder", page_icon="🚑", initial_sidebar_state="collapsed")

# Simple Mobile-Optimized CSS
st.markdown("""
<style>
    .stApp { margin-top: -50px; }
    .status-card {
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        color: white;
    }
    .status-active { background-color: #28a745; }
    .status-inactive { background-color: #6c757d; }
    .alert-card {
        background-color: #ffebee;
        border-left: 5px solid #dc3545;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    h1 { font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("🚑 First Responder App")

# --- Status Toggle ---
if "on_duty" not in st.session_state:
    st.session_state.on_duty = False

col1, col2 = st.columns([2, 1])
with col1:
    st.write(f"User: **Officer James Wilson**")
    st.caption("ID: pers-responder-001")

with col2:
    if st.button("Toggle"):
        st.session_state.on_duty = not st.session_state.on_duty

# Status Indicator
status_color = "status-active" if st.session_state.on_duty else "status-inactive"
status_text = "ON DUTY" if st.session_state.on_duty else "OFF DUTY"

st.markdown(f"""
<div class="status-card {status_color}">
    <h2>{status_text}</h2>
    <p>Last update: {datetime.now().strftime('%H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# --- Active Alerts Feed ---
st.subheader("Active Alerts")

if st.session_state.on_duty:
    # Simulated Alert Data (In real app, fetch from API)
    alerts = [
        {
            "id": "alert-101",
            "type": "FIRE",
            "time": "5 mins ago",
            "location": "Downtown District",
            "desc": "Smoke reported near Power Station",
            "priority": "HIGH"
        },
        {
            "id": "alert-102",
            "type": "SECURITY",
            "time": "15 mins ago",
            "location": "Sector 4",
            "desc": "Perimeter breach detected",
            "priority": "MEDIUM"
        }
    ]
    
    for alert in alerts:
        st.markdown(f"""
        <div class="alert-card">
            <h4>🚨 {alert['type']} - {alert['priority']}</h4>
            <p><strong>📍 {alert['location']}</strong> • {alert['time']}</p>
            <p>{alert['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Acknowledge {alert['id']}", key=alert['id']):
            st.success(f"Acknowledged {alert['id']}")
            time.sleep(1)
            st.rerun()
            
else:
    st.info("You are currently OFF DUTY. Go ON DUTY to receive alerts.")

# --- Installation Prompt ---
with st.expander("📱 Install App"):
    st.write("To install on iOS:")
    st.code("1. Tap 'Share'\n2. Select 'Add to Home Screen'")
    st.write("To install on Android:")
    st.code("1. Tap Menu (⋮)\n2. Select 'Install App' or 'Add to Home screen'")
