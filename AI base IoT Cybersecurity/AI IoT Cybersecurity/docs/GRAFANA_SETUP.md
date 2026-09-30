# Grafana + InfluxDB Setup

1. Install and start Docker Desktop.
2. From this project folder run `start_grafana.bat`.
3. Open Grafana at http://localhost:3000 (admin/admin for this local lab).
4. Start Mosquitto and the existing AI collector as usual.
5. In another terminal run `run_grafana_bridge.bat`.
6. Grafana will show the provisioned **AI IoT Cybersecurity Dashboard**.

The bridge reads the existing `data/telemetry.jsonl` and `data/anomaly_events.jsonl` and sends them to InfluxDB. The AI collector remains unchanged.

Dashboard panels include MQTT message rate, AI anomaly score, average payload size, average message interval, anomaly count, and a future-ready ultrasonic distance panel.

For non-lab use, change the example passwords/tokens and do not expose anonymous MQTT to the Internet.
