import os
import streamlit as st
import pandas as pd
import plotly.express as px
from influxdb_client_3 import InfluxDBClient3


# ============================================================
# WINDOWS / GRPC DNS FIX
# ============================================================

os.environ["GRPC_DNS_RESOLVER"] = "native"


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="AI IoT Cybersecurity Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

INFLUX_HOST = os.getenv(
    "INFLUX_URL",
    "us-east-1-1.aws.cloud2.influxdata.com"
)

INFLUX_HOST = (
    INFLUX_HOST
    .replace("https://", "")
    .replace("http://", "")
    .rstrip("/")
)

INFLUX_BUCKET = os.getenv(
    "INFLUX_BUCKET",
    "iot_security"
)

INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 16px;
        color: #777;
        margin-bottom: 20px;
    }

    .status-normal {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }

    .status-anomaly {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🛡️ AI-Powered IoT Cybersecurity Dashboard</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Real-time IoT telemetry, AI anomaly detection and security monitoring"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# INFLUXDB CLIENT
# ============================================================

@st.cache_resource
def get_client():
    if not INFLUX_TOKEN:
        return None

    try:
        client = InfluxDBClient3(
            host=INFLUX_HOST,
            database=INFLUX_BUCKET,
            token=INFLUX_TOKEN,
        )

        return client

    except Exception as e:
        st.error(f"InfluxDB connection error: {e}")
        return None


client = get_client()


# ============================================================
# CONNECTION STATUS
# ============================================================

if not INFLUX_TOKEN:

    st.error(
        "❌ INFLUX_TOKEN is not configured. "
        "Add INFLUX_TOKEN in Render → Environment Variables."
    )

    st.stop()


if client:

    st.success(
        f"🟢 Connected to InfluxDB Cloud | "
        f"Bucket: `{INFLUX_BUCKET}`"
    )

else:

    st.error("🔴 Could not create InfluxDB client.")

    st.stop()


# ============================================================
# QUERY FUNCTION
# ============================================================

def run_query(query):

    try:

        result = client.query(
            query=query,
            language="sql",
        )

        df = result.to_pandas()

        return df

    except Exception as e:

        st.error(f"InfluxDB query error: {e}")

        return pd.DataFrame()


# ============================================================
# TELEMETRY QUERY
# ============================================================

telemetry_query = """
SELECT *
FROM iot_telemetry
WHERE time >= now() - INTERVAL '24 hours'
ORDER BY time DESC
"""

telemetry = run_query(telemetry_query)


# ============================================================
# SECURITY EVENT QUERY
# ============================================================

security_query = """
SELECT *
FROM security_anomaly
WHERE time >= now() - INTERVAL '24 hours'
ORDER BY time DESC
"""

security = run_query(security_query)


# ============================================================
# TIME CONVERSION
# ============================================================

if not telemetry.empty and "time" in telemetry.columns:

    telemetry["time"] = pd.to_datetime(
        telemetry["time"],
        errors="coerce",
    )


if not security.empty and "time" in security.columns:

    security["time"] = pd.to_datetime(
        security["time"],
        errors="coerce",
    )


# ============================================================
# BASIC STATISTICS
# ============================================================

telemetry_count = len(telemetry)

if (
    not telemetry.empty
    and "device" in telemetry.columns
):

    device_count = telemetry["device"].nunique()

else:

    device_count = 0


anomaly_count = len(security)


# ============================================================
# SECURITY STATUS
# ============================================================

if anomaly_count > 0:

    security_status = "🚨 ANOMALY"

else:

    security_status = "🟢 NORMAL"


# ============================================================
# TOP METRICS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "📡 Telemetry Records",
        telemetry_count,
    )


with col2:

    st.metric(
        "🚨 Anomaly Events",
        anomaly_count,
    )


with col3:

    st.metric(
        "📱 Devices",
        device_count,
    )


with col4:

    st.metric(
        "🔐 Security Status",
        security_status,
    )


st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🛡️ Cybersecurity Monitor")

st.sidebar.markdown(
    """
    ### System Architecture

    **ESP32 / Simulator**
    
    ↓
    
    **MQTT / Mosquitto**
    
    ↓
    
    **AI Collector**
    
    ↓
    
    **InfluxDB Cloud**
    
    ↓
    
    **Streamlit Dashboard**
    """
)

st.sidebar.divider()

st.sidebar.write(
    f"**InfluxDB Host:** `{INFLUX_HOST}`"
)

st.sidebar.write(
    f"**Bucket:** `{INFLUX_BUCKET}`"
)

st.sidebar.write(
    "**Refresh:** 10 seconds"
)


# ============================================================
# TELEMETRY SECTION
# ============================================================

st.subheader("📡 IoT Telemetry")


if telemetry.empty:

    st.warning(
        "⚠️ No telemetry data found in the last 24 hours."
    )

else:

    display_columns = [
        c
        for c in [
            "time",
            "device",
            "topic",
            "message_rate",
            "average_size",
            "messages",
            "average_interval",
            "topic_count",
            "ai_score",
        ]
        if c in telemetry.columns
    ]

    st.dataframe(
        telemetry[display_columns].head(50),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MQTT MESSAGE RATE
# ============================================================

st.subheader("📈 MQTT Message Rate")


if (
    not telemetry.empty
    and "message_rate" in telemetry.columns
):

    graph_data = telemetry.sort_values("time")

    fig = px.line(
        graph_data,
        x="time",
        y="message_rate",
        color=(
            "device"
            if "device" in graph_data.columns
            else None
        ),
        markers=True,
        title="MQTT Message Rate",
    )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Messages / minute",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

else:

    st.info(
        "Message-rate data is not available."
    )


# ============================================================
# MQTT PAYLOAD SIZE
# ============================================================

st.subheader("📦 MQTT Payload Size")


if (
    not telemetry.empty
    and "average_size" in telemetry.columns
):

    graph_data = telemetry.sort_values("time")

    fig = px.line(
        graph_data,
        x="time",
        y="average_size",
        color=(
            "device"
            if "device" in graph_data.columns
            else None
        ),
        markers=True,
        title="Average MQTT Payload Size",
    )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Bytes",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

else:

    st.info(
        "Payload-size data is not available."
    )


# ============================================================
# AI ANOMALY SCORE
# ============================================================

st.subheader("🤖 AI Anomaly Detection")


if (
    not telemetry.empty
    and "ai_score" in telemetry.columns
):

    ai_data = telemetry.dropna(
        subset=["ai_score"]
    ).sort_values("time")

    if not ai_data.empty:

        fig = px.line(
            ai_data,
            x="time",
            y="ai_score",
            color=(
                "device"
                if "device" in ai_data.columns
                else None
            ),
            markers=True,
            title="AI Anomaly Score",
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            annotation_text="Anomaly threshold",
        )

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="AI Score",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:

        st.info(
            "No AI score values available yet."
        )

else:

    st.info(
        "AI score data is not available."
    )


# ============================================================
# SECURITY EVENTS
# ============================================================

st.subheader("🚨 Security Events")


if security.empty:

    st.success(
        "🟢 No anomaly events detected "
        "in the last 24 hours."
    )

else:

    security_display = [
        c
        for c in [
            "time",
            "device",
            "topic",
            "status",
            "ai_score",
            "reason",
        ]
        if c in security.columns
    ]

    st.dataframe(
        security[security_display].head(100),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ANOMALY SUMMARY
# ============================================================

if not security.empty:

    st.subheader("📊 Anomaly Summary")

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:

        if "device" in security.columns:

            device_anomalies = (
                security["device"]
                .value_counts()
                .reset_index()
            )

            device_anomalies.columns = [
                "device",
                "anomalies",
            ]

            fig = px.bar(
                device_anomalies,
                x="device",
                y="anomalies",
                title="Anomalies by Device",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    with summary_col2:

        if "topic" in security.columns:

            topic_anomalies = (
                security["topic"]
                .value_counts()
                .reset_index()
            )

            topic_anomalies.columns = [
                "topic",
                "anomalies",
            ]

            fig = px.bar(
                topic_anomalies,
                x="topic",
                y="anomalies",
                title="Anomalies by MQTT Topic",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# ============================================================
# SYSTEM ARCHITECTURE
# ============================================================

st.divider()

st.subheader("🏗️ System Architecture")

architecture = """
ESP32 / IoT Device
        ↓
Wi-Fi Network
        ↓
MQTT Broker (Mosquitto)
        ↓
Python AI Collector
        ↓
Isolation Forest
        +
Deterministic Security Rules
        ↓
InfluxDB Cloud
        ↓
Streamlit Dashboard
        +
Grafana
        +
Pushover Alert
"""

st.code(
    architecture,
    language="text",
)


# ============================================================
# PROJECT INFORMATION
# ============================================================

st.divider()

st.subheader("ℹ️ About the System")

st.markdown(
    """
    ### AI-Powered IoT Cybersecurity

    This dashboard monitors IoT device telemetry and
    identifies unusual behavior using:

    - MQTT telemetry monitoring
    - Device behavior profiling
    - Isolation Forest anomaly detection
    - Message-rate analysis
    - MQTT payload-size analysis
    - Topic-count monitoring
    - Security event logging
    - Real-time cloud visualization
    - Mobile security notifications

    **Important:** An anomaly indicates unusual behavior.
    It is not by itself proof of a cyberattack.
    """
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI-Powered IoT Cybersecurity | "
    "MQTT + Python + Isolation Forest + InfluxDB Cloud + Streamlit"
)

st.caption(
    "Dashboard refreshes automatically every 10 seconds."
)


# ============================================================
# AUTO REFRESH
# ============================================================

st.markdown(
    """
    <script>
    setTimeout(function(){
        window.parent.location.reload();
    }, 10000);
    </script>
    """,
    unsafe_allow_html=True,
)
