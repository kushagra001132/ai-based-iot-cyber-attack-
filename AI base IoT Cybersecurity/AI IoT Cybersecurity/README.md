# AI-Powered Autonomous IoT Cybersecurity & Source Tracing System

A complete local-lab project for:
- MQTT IoT telemetry collection
- Automatic device discovery
- Baseline learning
- Isolation Forest anomaly detection
- Deterministic safety checks for obvious abnormal traffic
- MQTT client/source-IP tracing from Mosquitto broker logs
- Attack/anomaly event logging
- Local test simulator
- ESP32 MQTT telemetry firmware
- Optional Grafana/InfluxDB integration notes

## Architecture

ESP32 / simulator
        |
        v
   Mosquitto MQTT
        |
        +----> AI Collector ----> anomaly_events.jsonl
        |
        +----> Mosquitto log ----> Source Tracer
                                  |
                                  v
                         client ID + source IP
                                  |
                                  v
                           anomaly correlation

IMPORTANT:
- Use this only on networks/devices you own or are authorized to test.
- The AI identifies unusual behavior; it does not prove that an attack occurred.
- A source IP identifies a network endpoint, not a human attacker.
- The included Mosquitto configuration is intentionally insecure for an isolated lab:
  allow_anonymous true and port 1883 without TLS. Never expose it to the Internet.

## Requirements

Windows + PowerShell
Python 3.10+ (tested design target: 3.13)
Mosquitto 2.x installed

Python packages:
    paho-mqtt
    numpy
    pandas
    scikit-learn

## Quick start

### 1. Create/activate venv

PowerShell:
    cd "C:\path\to\AI_IoT_Cybersecurity_COMPLETE"
    py -m venv iot_security_env
    .\iot_security_env\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt

### 2. Start Mosquitto

Edit mosquitto_lab.conf if your project folder path differs.

    cd "C:\Program Files\mosquitto"
    .\mosquitto.exe -c "C:\path\to\AI_IoT_Cybersecurity_COMPLETE\mosquitto_lab.conf" -v

Keep this terminal open.

### 3. Start AI collector

In a new terminal:
    cd "C:\path\to\AI_IoT_Cybersecurity_COMPLETE"
    .\iot_security_env\Scripts\Activate.ps1
    python collector.py

The collector learns 30 normal samples by default.

### 4. Start source tracer

In another terminal:
    python source_tracer.py

The tracer watches mosquitto.log and maintains source_map.json.

### 5. Run normal telemetry

In another terminal:
    python simulator.py --mode normal --device ESP32_01 --count 40 --interval 2

### 6. Run authorized anomaly simulation

    python simulator.py --mode burst --device ESP32_01 --count 100 --interval 0.05

or:

    python simulator.py --mode abnormal --device ESP32_01 --count 20 --interval 0.1

The collector combines Isolation Forest with transparent safety rules. This makes obvious rate/size/topic anomalies visible even when a small ML baseline would otherwise be too permissive.

## Files

collector.py
    MQTT collector + feature extraction + Isolation Forest + safety rules.

source_tracer.py
    Parses Mosquitto connection log lines and maps client IDs to source IPs.

simulator.py
    Generates normal, burst, abnormal, and mixed telemetry for authorized testing.

config.py
    Central configuration.

mosquitto_lab.conf
    Isolated-lab Mosquitto configuration.

esp32_mqtt_telemetry/
    Arduino/ESP32 firmware.

requirements.txt
    Python dependencies.

run_collector.bat
run_source_tracer.bat
run_normal_test.bat
run_burst_test.bat
    Windows shortcuts.

data/
    Runtime JSONL/JSON files are created here.

## AI interpretation

AI SCORE is Isolation Forest decision_function output. It is NOT an attack probability.

The final status is:
- NORMAL: ML and safety checks do not currently flag the observation.
- ANOMALY: ML or a deterministic safety rule flags the observation.

## Source tracing

The source tracer reads broker logs. With a local test using 127.0.0.1, the source will naturally be 127.0.0.1.
With a real ESP32 connecting over the LAN, the broker can see the ESP32's LAN endpoint address, subject to routing/NAT.

## ESP32

Open:
    esp32_mqtt_telemetry/esp32_mqtt_telemetry.ino

Install the PubSubClient library in Arduino IDE.
Set WIFI_SSID, WIFI_PASSWORD, and MQTT_SERVER to the PC's LAN IP.
Do NOT use 127.0.0.1 on the ESP32; that means the ESP32 itself.

## Next upgrades

For a production deployment:
- MQTT username/password
- TLS
- ACLs
- isolated VLAN
- firewall restrictions
- persistent database
- Grafana/InfluxDB
- model persistence/versioning
- authenticated device identity
- alerting and incident-response workflow
