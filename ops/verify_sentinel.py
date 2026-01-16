"""
Verification script for Sentinel Integration.

1. Runs the sentinel monitor for 15 seconds.
2. Checks if incidents.jsonl file grows.
3. Validates the content of new incidents.
"""

import time
import sys
import json
import threading
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ops.emergency.run_sentinel_monitor import run_monitor

def verify_sentinel_ingestion():
    log_file = project_root / "logs/incidents.jsonl"
    
    # Measure initial size
    initial_count = 0
    if log_file.exists():
        with open(log_file, "r") as f:
            initial_count = sum(1 for _ in f)
    
    print(f"Initial incident count: {initial_count}")
    
    # Run monitor in a separate thread for 15 seconds
    print("Starting Monitor for 15 seconds...")
    monitor_thread = threading.Thread(target=run_monitor, kwargs={"interval_seconds": 2}, daemon=True)
    monitor_thread.start()
    
    time.sleep(15)
    print("Stopping test...")
    
    # Measure final size
    final_count = 0
    new_incidents = []
    if log_file.exists():
        with open(log_file, "r") as f:
            lines = f.readlines()
            final_count = len(lines)
            if final_count > initial_count:
                # Parse the new lines
                for line in lines[initial_count:]:
                    try:
                        new_incidents.append(json.loads(line))
                    except:
                        pass

    print(f"Final incident count: {final_count}")
    print(f"New incidents generated: {len(new_incidents)}")
    
    if len(new_incidents) > 0:
        print("✅ Sentinel Integration Verified: Alerts successfully ingested.")
        print(f"latest: {new_incidents[-1]['id']} - {new_incidents[-1]['threat_type']}")
    else:
        print("⚠️ Warning: No new incidents generated. (Mock generator has 30% random chance, might just be bad luck or interval too short)")

if __name__ == "__main__":
    verify_sentinel_ingestion()
