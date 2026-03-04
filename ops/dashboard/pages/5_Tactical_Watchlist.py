import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import uuid

# Add project root to path to allow importing ops modules
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

from ops.dashboard.auth import require_auth, get_current_user
from ops.emergency.watchlist_manager import WatchlistManager

@require_auth(role="Operator")
def main():
    st.set_page_config(page_title="Tactical Watchlist", page_icon="🕵️", layout="wide")

    # Inject custom branding from Home if available, otherwise use default
    st.markdown("""
    <div style="background-color: #0d1117; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545; margin-bottom: 25px;">
        <h1 style="color: #ffffff; margin: 0;">🕵️ Tactical Watchlist: Pre-Threat Prevention</h1>
        <p style="color: #6c757d; margin: 5px 0 0 0;">Manage insecure vehicle and individual databases to proactively neutralize threats.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Initialize Watchlist Manager ---
    db_path = project_root / "ops" / "emergency" / "data" / "tactical_watchlist.json"
    wm = WatchlistManager(db_path=str(db_path))

    # --- User Info & Context ---
    user = get_current_user()
    
    with st.sidebar:
        st.header("👤 Security Operator")
        if user:
            st.write(f"**{user.get('displayName', 'Unknown')}**")
            st.caption(f"Role: Operator")
        st.divider()
        
        st.header("🏢 Mission Context")
        st.info("Watchlist matches trigger **CRITICAL** escalation and immediate SATRECON downlinks.")

    tab_v, tab_i, tab_stats = st.tabs(["🚗 Insecure Vehicles", "👤 Suspected Individuals", "📊 Watchlist Intel"])

    # --- VEHICLES TAB ---
    with tab_v:
        st.subheader("Blacklisted Vehicle Database")
        vehicles = wm.watchlist.get("vehicles", [])
        
        if vehicles:
            df_v = pd.DataFrame(vehicles)
            # Reorder columns for display
            cols = ["id", "type", "color", "risk_level", "reason"]
            df_v = df_v[[c for c in cols if c in df_v.columns]]
            
            # Styling the dataframe (highlighting CRITICAL risk)
            def highlight_risk(val):
                color = '#dc3545' if val == 'CRITICAL' else '#ffc107' if val == 'HIGH' else '#17a2b8'
                return f'color: {color}; font-weight: bold'

            st.dataframe(df_v.style.map(highlight_risk, subset=['risk_level']), use_container_width=True)
            
            # Delete selection
            with st.expander("🗑️ Remove from Watchlist"):
                to_delete = st.selectbox("Select Vehicle ID to Remove", options=[v["id"] for v in vehicles])
                if st.button("Delete Entry", type="primary"):
                    wm.watchlist["vehicles"] = [v for v in vehicles if v["id"] != to_delete]
                    wm.save_database()
                    st.success(f"Removed vehicle {to_delete} from database.")
                    st.rerun()
        else:
            st.info("No vehicles currently on the watchlist.")

        st.markdown("---")
        with st.expander("➕ Add Insecure Vehicle", expanded=False):
            with st.form("new_vehicle"):
                col1, col2 = st.columns(2)
                with col1:
                    v_id = st.text_input("Vehicle Plate / ID", placeholder="e.g., V-NYC-1234")
                    v_type = st.selectbox("Vehicle Type", ["SUV", "Truck", "Sedan", "Motorcycle", "Van", "Drone"])
                with col2:
                    v_color = st.text_input("Color", placeholder="e.g., Black")
                    v_risk = st.selectbox("Risk Level", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
                
                v_reason = st.text_area("Reason for Watchlist", placeholder="Prior breach history, reported stolen, etc.")
                
                if st.form_submit_button("Add to Database"):
                    if not v_id:
                        st.error("Vehicle ID is required.")
                    else:
                        wm.add_to_watchlist("vehicles", {
                            "id": v_id,
                            "type": v_type,
                            "color": v_color,
                            "risk_level": v_risk,
                            "reason": v_reason,
                            "timestamp": str(uuid.uuid4()) # For uniqueness if needed
                        })
                        st.success(f"Vehicle {v_id} added to tactical watchlist.")
                        st.rerun()

    # --- INDIVIDUALS TAB ---
    with tab_i:
        st.subheader("Suspected Individuals Database")
        individuals = wm.watchlist.get("individuals", [])
        
        if individuals:
            df_i = pd.DataFrame(individuals)
            cols = ["id", "name", "risk_level", "reason"]
            df_i = df_i[[c for c in cols if c in df_i.columns]]
            st.dataframe(df_i, use_container_width=True)
            
            with st.expander("🗑️ Remove Suspect"):
                to_delete_p = st.selectbox("Select Suspect ID to Remove", options=[i["id"] for i in individuals])
                if st.button("Delete Suspect Entry", type="primary"):
                    wm.watchlist["individuals"] = [i for i in individuals if i["id"] != to_delete_p]
                    wm.save_database()
                    st.success(f"Removed suspect {to_delete_p} from database.")
                    st.rerun()
        else:
            st.info("No individuals currently on the watchlist.")

        st.markdown("---")
        with st.expander("➕ Add Suspected Individual", expanded=False):
            with st.form("new_person"):
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    p_id = st.text_input("Subject ID / Alias", placeholder="e.g., S-RED-ALPHA")
                with col_p2:
                    p_name = st.text_input("Known Name", placeholder="e.g., John Doe")
                
                p_risk = st.selectbox("Risk Level", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], key="p_risk")
                p_reason = st.text_area("Reason for Watchlist", placeholder="Unauthorized access attempt, etc.", key="p_reason")
                
                if st.form_submit_button("Flag Individual"):
                    if not p_id:
                        st.error("Subject ID is required.")
                    else:
                        wm.add_to_watchlist("individuals", {
                            "id": p_id,
                            "name": p_name,
                            "risk_level": p_risk,
                            "reason": p_reason
                        })
                        st.success(f"Subject {p_id} flagged for proactive prevention.")
                        st.rerun()

    # --- STATS TAB ---
    with tab_stats:
        st.subheader("Watchlist Intelligence Summary")
        v_count = len(wm.watchlist.get("vehicles", []))
        p_count = len(wm.watchlist.get("individuals", []))
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tracked Vehicles", v_count)
        c2.metric("Tracked Suspects", p_count)
        c3.metric("Database Health", "SYNCED", delta="Active")
        
        st.info("Intel from the **Active Learning** loop automatically feeds into the suggested watchlist entries below.")
        st.caption("Note: Future versions will include automated license plate and facial recognition signature syncing.")

if __name__ == "__main__":
    main()
