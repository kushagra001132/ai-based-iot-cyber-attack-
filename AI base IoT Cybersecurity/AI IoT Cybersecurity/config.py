from pathlib import Path

BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "iot/+/#"

LEARNING_SAMPLES = 30
WINDOW_SIZE = 60

MODEL_ESTIMATORS = 200
CONTAMINATION = 0.10
RANDOM_STATE = 42

# Transparent deterministic safety checks.
MAX_MSG_RATE_PER_MIN = 90.0
MAX_AVG_SIZE_BYTES = 1500.0
MAX_TOPIC_COUNT = 5
MIN_AVG_GAP_SECONDS = 0.20

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

EVENT_LOG = DATA_DIR / "anomaly_events.jsonl"
TELEMETRY_LOG = DATA_DIR / "telemetry.jsonl"
SOURCE_MAP = DATA_DIR / "source_map.json"
MOSQUITTO_LOG = PROJECT_DIR / "mosquitto.log"
