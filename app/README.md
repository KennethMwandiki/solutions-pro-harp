# Orbital Inference Container

Runs ONNX models for anomaly detection (person, vehicle, drone, excavator) and emits minimal, signed alerts with geo metadata.

- Configure thresholds with env vars.
- Replace `models/vehicle_person_uav.onnx` with your trained model.
- Integrate `frame_stream.py` with real SDK host camera interfaces.

## Quick start (local simulation)
- Place sample frames under `/tmp/frames`.
- Run: `STREAM_SOURCE=local_dir python src/main.py`
