"""
Sentinel Monitor Service.

This script runs a continuous loop to poll the Azure Sentinel Connector
for new alerts and processes them via the EventProcessor.
"""

import time
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from ops.emergency.sentinel_connector import SentinelConnector
from ops.emergency.event_processor import EventProcessor
from ops.emergency.data_models import EntityRepository
from ops.emergency.sample_data import generate_sample_data

def run_monitor(interval_seconds: int = 10):
    print(f"🚀 Starting Sentinel Monitor (Poll Interval: {interval_seconds}s)")
    
    # Initialize components
    connector = SentinelConnector()
    processor = EventProcessor(
        config_path=str(project_root / "ops/emergency/config.yaml"),
        log_dir=str(project_root / "logs")
    )
    
    # Initialize Entity Repo
    # In prod this would load from DB/File. For now we use the sample data generator
    print("📂 Loading Entity Repository...")
    entity_repo = generate_sample_data()
    
    mode_str = "MOCK MODE" if connector.mock_mode else "REAL AZURE MODE"
    print(f"📡 Connector initialized in {mode_str}")
    
    try:
        while True:
            # 1. Fetch
            alerts = connector.fetch_recent_alerts()
            
            if alerts:
                print(f"⚡ Received {len(alerts)} new alerts from Sentinel.")
                
                # 2. Process
                for alert in alerts:
                    incident = processor.process_event(alert, entity_repo)
                    if incident:
                        print(f"  ✅ Created Incident {incident.id} [Risk: {incident.risk_score:.2f}]")
                    else:
                        print(f"  ⚠️ Alert {alert.id} filtered or error processing.")
            else:
                # No alerts, just heartbeat
                # print(".", end="", flush=True) 
                pass
                
            # 3. Wait
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping Sentinel Monitor...")

if __name__ == "__main__":
    run_monitor()
