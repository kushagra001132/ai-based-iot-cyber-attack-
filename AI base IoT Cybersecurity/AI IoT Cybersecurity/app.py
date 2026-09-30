import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(
    page_title="AI IoT Cybersecurity",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AI-Powered IoT Cybersecurity Dashboard")
st.caption("AI-Based IoT Cyberattack and Device Anomaly Detection")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

telemetry_file = DATA_DIR / "telemetry.jsonl"
anomaly_file = DATA_DIR / "anomaly_events.jsonl"


def load_jsonl(file_path):
    if not file_path.exists():
        return pd.DataFrame()

    rows = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return pd.DataFrame(rows)


telemetry = load_jsonl(telemetry_file)
anomalies = load_jsonl(anomaly_file)


# -------------------------
# TOP METRICS
# -------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Telemetry Records",
        len(telemetry)
    )

with col2:
    st.metric(
        "Anomaly Events",
        len(anomalies)
    )

with col3:
    if not telemetry.empty and "device" in telemetry.columns:
        devices = telemetry["device"].nunique()
    else:
        devices = 0

    st.metric(
        "Devices",
        devices
    )

with col4:
    if not anomalies.empty and "status" in anomalies.columns:
        status = "ANOMALY DETECTED"
    else:
        status = "NORMAL"

    st.metric(
        "Security Status",
        status
    )


st.divider()


# -------------------------
# TELEMETRY
# -------------------------

st.header("📡 IoT Telemetry")

if telemetry.empty:

    st.warning(
        "No telemetry data found. "
        "Run the MQTT collector first and make sure "
        "data/telemetry.jsonl exists."
    )

else:

    st.dataframe(
        telemetry.tail(20),
        use_container_width=True
    )


# -------------------------
# AI ANOMALY SCORE
# -------------------------

st.header("🤖 AI Anomaly Detection")

if not anomalies.empty:

    if "ai_score" in anomalies.columns:

        chart_data = anomalies.copy()

        if "time" in chart_data.columns:
            chart_data["time"] = pd.to_datetime(
                chart_data["time"],
                errors="coerce"
            )

            chart_data = chart_data.dropna(
                subset=["time"]
            )

            chart_data = chart_data.set_index("time")

        st.line_chart(
            chart_data["ai_score"]
        )

    else:

        st.info(
            "AI score field was not found in anomaly data."
        )

else:

    st.info(
        "No anomaly events detected yet."
    )


# -------------------------
# MESSAGE RATE
# -------------------------

st.header("📈 MQTT Message Rate")

if not telemetry.empty:

    if "message_rate" in telemetry.columns:

        rate_data = telemetry.copy()

        if "time" in rate_data.columns:
            rate_data["time"] = pd.to_datetime(
                rate_data["time"],
                errors="coerce"
            )

            rate_data = rate_data.dropna(
                subset=["time"]
            )

            rate_data = rate_data.set_index("time")

        st.line_chart(
            rate_data["message_rate"]
        )

    else:

        st.info(
            "message_rate field not found."
        )


# -------------------------
# PAYLOAD SIZE
# -------------------------

st.header("📦 MQTT Payload Size")

if not telemetry.empty:

    size_field = None

    if "average_size" in telemetry.columns:
        size_field = "average_size"

    elif "size" in telemetry.columns:
        size_field = "size"

    if size_field:

        size_data = telemetry.copy()

        if "time" in size_data.columns:
            size_data["time"] = pd.to_datetime(
                size_data["time"],
                errors="coerce"
            )

            size_data = size_data.dropna(
                subset=["time"]
            )

            size_data = size_data.set_index("time")

        st.line_chart(
            size_data[size_field]
        )

    else:

        st.info(
            "Payload size field not found."
        )


# -------------------------
# SECURITY EVENTS
# -------------------------

st.header("🚨 Security Events")

if not anomalies.empty:

    st.dataframe(
        anomalies.tail(30),
        use_container_width=True
    )

else:

    st.success(
        "No anomaly events recorded."
    )


# -------------------------
# PROJECT INFORMATION
# -------------------------

st.divider()

st.header("ℹ️ System Architecture")

st.code(
"""ESP32 / IoT Device
        ↓
      Wi-Fi
        ↓
   MQTT Broker
   (Mosquitto)
        ↓
 Python AI Collector
        ↓
  Isolation Forest
        ↓
Normal / Anomalous
        ↓
 JSONL / InfluxDB
        ↓
 Streamlit Dashboard
""",
language="text"
)

st.caption(
    "Note: An anomaly indicates unusual behavior and "
    "is not by itself proof of a cyberattack."
)