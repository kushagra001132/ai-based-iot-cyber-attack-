import json
import time
import threading
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import paho.mqtt.client as mqtt
from sklearn.ensemble import IsolationForest

# Windows alarm
try:
    import winsound
    WINDOWS_SOUND_AVAILABLE = True
except ImportError:
    WINDOWS_SOUND_AVAILABLE = False

# Pushover
try:
    from pushover_alert import send_pushover
    PUSHOVER_AVAILABLE = True
except ImportError:
    PUSHOVER_AVAILABLE = False


# ============================================================
# CONFIGURATION
# ============================================================

BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "iot/+/#"

LEARNING_SAMPLES = 30

MODEL_ESTIMATORS = 200
CONTAMINATION = 0.10
RANDOM_STATE = 42

# Deterministic security rules
MAX_MSG_RATE_PER_MIN = 90.0
MAX_AVG_SIZE_BYTES = 1500.0
MAX_TOPIC_COUNT = 5
MIN_AVG_GAP_SECONDS = 0.20

# Alert/alarm cooldown
ALERT_COOLDOWN = 60


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

EVENT_LOG = DATA_DIR / "anomaly_events.jsonl"
TELEMETRY_LOG = DATA_DIR / "telemetry.jsonl"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# GLOBAL STATE
# ============================================================

devices = {}
models = {}

last_alert_time = defaultdict(float)

state_lock = threading.Lock()


# ============================================================
# DEVICE STATE
# ============================================================

def create_device_state():

    return {
        "first_seen": time.time(),
        "last_seen": time.time(),

        "messages": 0,

        "timestamps": deque(maxlen=1000),
        "sizes": deque(maxlen=1000),
        "topics": set(),

        "baseline_features": [],
        "baseline_ready": False,

        "last_ai_score": None,
    }


# ============================================================
# JSONL WRITER
# ============================================================

def write_jsonl(file_path, data):

    try:

        with open(file_path, "a", encoding="utf-8") as f:

            f.write(
                json.dumps(
                    data,
                    ensure_ascii=False
                )
                + "\n"
            )

    except Exception as e:

        print("❌ JSONL write error:", e)


# ============================================================
# WINDOWS ALARM
# ============================================================

def play_alarm():

    if not WINDOWS_SOUND_AVAILABLE:

        print("🔊 Alarm unavailable on this operating system.")

        return

    def alarm_thread():

        try:

            print("\n🔊🔊🔊 SECURITY ALARM 🔊🔊🔊")

            # Three-beep alarm
            for _ in range(3):

                winsound.Beep(1500, 500)

                time.sleep(0.15)

                winsound.Beep(800, 500)

                time.sleep(0.20)

        except Exception as e:

            print("❌ Alarm error:", e)

    # Don't block MQTT processing
    threading.Thread(
        target=alarm_thread,
        daemon=True
    ).start()


# ============================================================
# PUSHOVER + ALARM
# ============================================================

def send_security_alert(
    device,
    topic,
    ai_score,
    message_rate,
    average_size,
    topic_count,
    average_interval,
    reason
):

    current_time = time.time()

    with state_lock:

        previous_alert = last_alert_time[device]

        if current_time - previous_alert < ALERT_COOLDOWN:

            return

        last_alert_time[device] = current_time

    # --------------------------------------------------------
    # SOUND ALARM
    # --------------------------------------------------------

    play_alarm()

    # --------------------------------------------------------
    # PUSHOVER
    # --------------------------------------------------------

    message = (
        f"Device: {device}\n"
        f"Topic: {topic}\n"
        f"AI Score: {ai_score:.4f}\n"
        f"Message Rate: {message_rate:.2f}/min\n"
        f"Avg Size: {average_size:.2f} bytes\n"
        f"Topics: {topic_count}\n"
        f"Avg Gap: {average_interval:.2f} sec\n"
        f"Reason: {reason}\n\n"
        f"Note: Anomaly indicates unusual behavior; "
        f"it is not by itself proof of an attack."
    )

    if PUSHOVER_AVAILABLE:

        try:

            success = send_pushover(
                "🚨 IoT SECURITY ALERT",
                message
            )

            if success:

                print("📱 PUSHOVER ALERT SENT")

            else:

                print("⚠️ Pushover notification failed")

        except Exception as e:

            print("❌ Pushover error:", e)

    else:

        print("⚠️ pushover_alert.py not available")


# ============================================================
# FEATURE CALCULATION
# ============================================================

def calculate_features(device):

    state = devices[device]

    timestamps = list(state["timestamps"])
    sizes = list(state["sizes"])
    topics = state["topics"]

    message_count = state["messages"]

    # -----------------------------------------
    # Message rate
    # -----------------------------------------

    message_rate = 0.0

    if len(timestamps) >= 2:

        elapsed = timestamps[-1] - timestamps[0]

        if elapsed > 0:

            message_rate = (
                (len(timestamps) - 1)
                / elapsed
                * 60
            )

    # -----------------------------------------
    # Average payload size
    # -----------------------------------------

    average_size = 0.0

    if sizes:

        average_size = float(
            np.mean(sizes)
        )

    # -----------------------------------------
    # Topic count
    # -----------------------------------------

    topic_count = len(topics)

    # -----------------------------------------
    # Average message interval
    # -----------------------------------------

    average_interval = 0.0

    if len(timestamps) >= 2:

        gaps = np.diff(timestamps)

        if len(gaps) > 0:

            average_interval = float(
                np.mean(gaps)
            )

    return {
        "message_rate": float(message_rate),
        "average_size": float(average_size),
        "topic_count": int(topic_count),
        "average_interval": float(average_interval),
        "messages": int(message_count),
    }


# ============================================================
# DETERMINISTIC SECURITY RULES
# ============================================================

def check_security_rules(features):

    reasons = []

    if (
        features["message_rate"]
        > MAX_MSG_RATE_PER_MIN
    ):

        reasons.append(
            f"message rate > {MAX_MSG_RATE_PER_MIN:.0f}/min"
        )

    if (
        features["average_size"]
        > MAX_AVG_SIZE_BYTES
    ):

        reasons.append(
            f"average payload size > "
            f"{MAX_AVG_SIZE_BYTES:.0f} bytes"
        )

    if (
        features["topic_count"]
        > MAX_TOPIC_COUNT
    ):

        reasons.append(
            f"topic count > {MAX_TOPIC_COUNT}"
        )

    if (
        features["average_interval"] > 0
        and
        features["average_interval"]
        < MIN_AVG_GAP_SECONDS
    ):

        reasons.append(
            f"average interval < "
            f"{MIN_AVG_GAP_SECONDS:.2f} sec"
        )

    return reasons


# ============================================================
# ISOLATION FOREST
# ============================================================

def train_model(device):

    state = devices[device]

    if len(state["baseline_features"]) < LEARNING_SAMPLES:

        return False

    try:

        X = np.array(
            state["baseline_features"],
            dtype=float
        )

        model = IsolationForest(
            n_estimators=MODEL_ESTIMATORS,
            contamination=CONTAMINATION,
            random_state=RANDOM_STATE
        )

        model.fit(X)

        models[device] = model

        state["baseline_ready"] = True

        print(
            f"\n🤖 AI BASELINE READY: "
            f"{device} | "
            f"{len(X)}/{LEARNING_SAMPLES}"
        )

        return True

    except Exception as e:

        print(
            f"❌ Model training error for "
            f"{device}: {e}"
        )

        return False


# ============================================================
# ANOMALY ANALYSIS
# ============================================================

def analyze_device(
    device,
    topic,
    features
):

    state = devices[device]

    feature_vector = np.array(
        [[
            features["message_rate"],
            features["average_size"],
            features["topic_count"],
            features["average_interval"],
        ]],
        dtype=float
    )

    # --------------------------------------------------------
    # BASELINE LEARNING
    # --------------------------------------------------------

    if not state["baseline_ready"]:

        state["baseline_features"].append(
            feature_vector[0].tolist()
        )

        current_count = len(
            state["baseline_features"]
        )

        print(
            f"AI BASELINE: "
            f"{device} "
            f"{current_count}/{LEARNING_SAMPLES}"
        )

        if current_count >= LEARNING_SAMPLES:

            train_model(device)

        return False, 0.0, []

    # --------------------------------------------------------
    # ISOLATION FOREST
    # --------------------------------------------------------

    ai_score = 0.0

    ai_anomaly = False

    if device in models:

        try:

            model = models[device]

            ai_score = float(
                model.decision_function(
                    feature_vector
                )[0]
            )

            prediction = int(
                model.predict(
                    feature_vector
                )[0]
            )

            ai_anomaly = prediction == -1

        except Exception as e:

            print(
                f"❌ AI analysis error: {e}"
            )

    # --------------------------------------------------------
    # DETERMINISTIC RULES
    # --------------------------------------------------------

    rule_reasons = check_security_rules(
        features
    )

    rule_anomaly = len(rule_reasons) > 0

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    anomaly = (
        ai_anomaly
        or
        rule_anomaly
    )

    reasons = []

    if ai_anomaly:

        reasons.append(
            "Isolation Forest detected unusual behavior"
        )

    reasons.extend(rule_reasons)

    state["last_ai_score"] = ai_score

    return anomaly, ai_score, reasons


# ============================================================
# MQTT CALLBACK
# ============================================================

def on_connect(client, userdata, flags, reason_code, properties=None):

    if reason_code == 0:

        print(
            f"[+] Connected to MQTT broker "
            f"{BROKER}:{PORT}"
        )

        client.subscribe(TOPIC)

        print(
            f"[+] Monitoring topic: {TOPIC}"
        )

        print(
            "[+] Automatic device discovery: ENABLED"
        )

        print(
            f"[+] AI baseline learning: "
            f"{LEARNING_SAMPLES} samples/device"
        )

    else:

        print(
            f"❌ MQTT connection failed. "
            f"Reason code: {reason_code}"
        )


# ============================================================
# MQTT MESSAGE CALLBACK
# ============================================================

def on_message(client, userdata, msg):

    device = "UNKNOWN"

    try:

        topic = msg.topic

        payload = msg.payload

        payload_size = len(payload)

        # ----------------------------------------------------
        # DEVICE EXTRACTION
        # ----------------------------------------------------

        topic_parts = topic.split("/")

        if (
            len(topic_parts) >= 2
            and topic_parts[0] == "iot"
        ):

            device = topic_parts[1]

        else:

            device = "UNKNOWN"

        # ----------------------------------------------------
        # CREATE DEVICE
        # ----------------------------------------------------

        if device not in devices:

            devices[device] = create_device_state()

            print(
                f"\n🔎 NEW DEVICE DISCOVERED: "
                f"{device}"
            )

        state = devices[device]

        current_time = time.time()

        # ----------------------------------------------------
        # UPDATE STATE
        # ----------------------------------------------------

        state["messages"] += 1

        state["last_seen"] = current_time

        state["timestamps"].append(
            current_time
        )

        state["sizes"].append(
            payload_size
        )

        state["topics"].add(
            topic
        )

        # ----------------------------------------------------
        # FEATURES
        # ----------------------------------------------------

        features = calculate_features(
            device
        )

        # ----------------------------------------------------
        # PAYLOAD PARSING
        # ----------------------------------------------------

        payload_json = None

        try:

            payload_text = payload.decode(
                "utf-8",
                errors="replace"
            )

            payload_json = json.loads(
                payload_text
            )

        except Exception:

            payload_text = "<non-JSON payload>"

        # ----------------------------------------------------
        # AI ANALYSIS
        # ----------------------------------------------------

        anomaly, ai_score, reasons = (
            analyze_device(
                device,
                topic,
                features
            )
        )

        status = (
            "ANOMALY"
            if anomaly
            else "NORMAL"
        )

        # ----------------------------------------------------
        # TELEMETRY RECORD
        # ----------------------------------------------------

        telemetry_record = {

            "time": time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),

            "epoch": current_time,

            "device": device,

            "topic": topic,

            "size": payload_size,

            "messages": features[
                "messages"
            ],

            "message_rate": features[
                "message_rate"
            ],

            "average_size": features[
                "average_size"
            ],

            "topic_count": features[
                "topic_count"
            ],

            "average_interval": features[
                "average_interval"
            ],

            "ai_score": ai_score,

            "status": status,
        }

        # Include JSON payload fields if available
        if isinstance(
            payload_json,
            dict
        ):

            for key in [
                "temperature",
                "distance",
                "status",
            ]:

                if key in payload_json:

                    telemetry_record[
                        key
                    ] = payload_json[key]

        write_jsonl(
            TELEMETRY_LOG,
            telemetry_record
        )

        # ----------------------------------------------------
        # TERMINAL DISPLAY
        # ----------------------------------------------------

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"DEVICE     : {device}"
        )

        print(
            f"TOPIC      : {topic}"
        )

        print(
            f"SIZE       : {payload_size} bytes"
        )

        print(
            f"MESSAGES   : "
            f"{features['messages']}"
        )

        print(
            f"MSG RATE   : "
            f"{features['message_rate']:.2f} msg/min"
        )

        print(
            f"AVG SIZE   : "
            f"{features['average_size']:.2f} bytes"
        )

        print(
            f"TOPICS     : "
            f"{features['topic_count']}"
        )

        print(
            f"AVG GAP    : "
            f"{features['average_interval']:.2f} sec"
        )

        print(
            f"AI SCORE   : "
            f"{ai_score:.4f}"
        )

        if anomaly:

            print(
                "STATUS     : 🚨 ANOMALY DETECTED"
            )

            if reasons:

                print(
                    "REASON     : "
                    + "; ".join(reasons)
                )

        else:

            print(
                "STATUS     : ✅ NORMAL"
            )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # ANOMALY EVENT
        # ----------------------------------------------------

        if anomaly:

            reason_text = (
                "; ".join(reasons)
                if reasons
                else "Unusual behavior detected"
            )

            anomaly_record = {

                "time": time.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),

                "epoch": current_time,

                "device": device,

                "topic": topic,

                "status": "ANOMALY",

                "ai_score": ai_score,

                "message_rate": features[
                    "message_rate"
                ],

                "average_size": features[
                    "average_size"
                ],

                "topic_count": features[
                    "topic_count"
                ],

                "average_interval": features[
                    "average_interval"
                ],

                "reason": reason_text,

                "note":
                    "Unusual behavior detected; "
                    "this is not proof of an attack.",
            }

            write_jsonl(
                EVENT_LOG,
                anomaly_record
            )

            # ------------------------------------------------
            # ALERT + ALARM
            # ------------------------------------------------

            send_security_alert(

                device=device,

                topic=topic,

                ai_score=ai_score,

                message_rate=features[
                    "message_rate"
                ],

                average_size=features[
                    "average_size"
                ],

                topic_count=features[
                    "topic_count"
                ],

                average_interval=features[
                    "average_interval"
                ],

                reason=reason_text,
            )

    except Exception as e:

        print(
            f"❌ Message processing error "
            f"for device {device}: {e}"
        )


# ============================================================
# MQTT DISCONNECT
# ============================================================

def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties=None
):

    print(
        f"⚠️ MQTT disconnected. "
        f"Reason: {reason_code}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "AI IoT CYBERSECURITY COLLECTOR"
    )

    print("=" * 70)

    print(
        f"Broker      : {BROKER}:{PORT}"
    )

    print(
        f"Topic       : {TOPIC}"
    )

    print(
        f"Baseline    : "
        f"{LEARNING_SAMPLES} samples/device"
    )

    print(
        f"AI Model    : Isolation Forest"
    )

    print(
        f"Alarm       : "
        f"{'ENABLED' if WINDOWS_SOUND_AVAILABLE else 'DISABLED'}"
    )

    print(
        f"Pushover    : "
        f"{'ENABLED' if PUSHOVER_AVAILABLE else 'DISABLED'}"
    )

    print("=" * 70)

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="AI_SECURITY_COLLECTOR"
    )

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:

        client.connect(
            BROKER,
            PORT,
            keepalive=60
        )

    except Exception as e:

        print(
            f"❌ Could not connect to MQTT broker: {e}"
        )

        return

    try:

        client.loop_forever()

    except KeyboardInterrupt:

        print(
            "\n🛑 Collector stopped."
        )

        client.disconnect()


if __name__ == "__main__":

    main()