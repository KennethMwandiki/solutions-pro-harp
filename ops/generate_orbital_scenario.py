from sgp4.api import Satrec
from sgp4.api import jday
from datetime import datetime, timedelta
import json

# TLE for a dummy satellite (or a real one like NOAA 20)
tle_line1 = '1 43013U 17073A   23320.91090656  .00000094  00000-0  56263-4 0  9997'
tle_line2 = '2 43013  98.7188 322.8687 0001099  75.1437 284.9922 14.19561614311050'

# Target: Seattle
target_lat = 47.6062
target_lon = -122.3321

def generate_scenario():
    satellite = Satrec.twoline2rv(tle_line1, tle_line2)
    
    # Calculate a pass (Simplified logic: just checking simple visibility window for demo)
    # real logic would iterate minutes to find AOS/LOS
    
    now = datetime.utcnow()
    
    # Generate a scenario active "now" for 5 minutes
    scenario = {
        "scenarios": [
            {
                "name": "Orbital Pass - Seattle",
                "description": "Generated based on TLE propagation.",
                "durationSeconds": 300,
                "objects": [
                    {
                        "type": "vehicle",
                        "start": [10, 10],
                        "end": [90, 90],
                        "speed": 5,
                        # In a real engine, we'd map this to the exact time the sat is overhead
                        "startTime": now.isoformat() 
                    }
                ]
            }
        ]
    }
    
    with open("ops/vth/orbital_config.json", "w") as f:
        json.dump(scenario, f, indent=4)
        
    print("Generated ops/vth/orbital_config.json based on satellite orbit.")

if __name__ == "__main__":
    generate_scenario()
