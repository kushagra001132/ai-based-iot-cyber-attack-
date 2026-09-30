# Project Flow

## Stage 1
ESP32 or simulator publishes MQTT telemetry.

## Stage 2
Mosquitto receives MQTT messages.

## Stage 3
collector.py automatically discovers devices from the device field or topic.

## Stage 4
Four behavior features are extracted:
1. message rate
2. average payload size
3. topic count
4. average message gap

## Stage 5
The first N samples become the device baseline.

## Stage 6
Isolation Forest scores future observations.

## Stage 7
Transparent safety checks catch obvious high-rate, large-payload, excessive-topic,
or very-short-interval behavior.

## Stage 8
Anomaly events are written to data/anomaly_events.jsonl.

## Stage 9
source_tracer.py watches Mosquitto's broker log and maps MQTT client IDs to source IPs.

## Limitation
The collector itself receives MQTT application data, not the TCP peer address.
Therefore source IP tracing is performed from the broker log, where the broker sees
the network connection.

## Recommended future architecture

MQTT Broker
    |
    +--> Collector
    |       |
    |       +--> ML + rules
    |       +--> anomaly_events.jsonl
    |
    +--> Broker log
            |
            +--> Source tracer
                    |
                    +--> source_map.json

A production version should use a database/event bus to correlate these streams by
timestamp and client ID.
