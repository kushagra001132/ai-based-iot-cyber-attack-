# Optional Grafana / InfluxDB Layer

The core project does not require Grafana or InfluxDB.

If you want a live dashboard later, use this data flow:

collector.py
    -> InfluxDB
    -> Grafana

Suggested panels:
- device count
- messages/minute
- average payload size
- average interval
- anomaly count
- AI score over time
- source IP/client ID
- latest anomaly table

For the first working demo, keep the JSONL logs. Add a database after the detection
pipeline is stable.
