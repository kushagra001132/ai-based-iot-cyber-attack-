import json
import re
import time
from pathlib import Path

from config import MOSQUITTO_LOG, SOURCE_MAP

# Handles common Mosquitto 2.x connection log forms.
PATTERNS = [
    re.compile(
        r"New client connected from (?P<ip>[0-9a-fA-F:.]+):\d+ as (?P<client>\S+)"
    ),
    re.compile(
        r"New connection from (?P<ip>[0-9a-fA-F:.]+):\d+"
    ),
    re.compile(
        r"Client (?P<client>\S+) connected from (?P<ip>[0-9a-fA-F:.]+)"
    ),
]


def load_map():
    if SOURCE_MAP.exists():
        try:
            return json.loads(SOURCE_MAP.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_map(data):
    SOURCE_MAP.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def process_line(line, data):
    matched = False

    for p in PATTERNS:
        m = p.search(line)
        if m:
            ip = m.groupdict().get("ip")
            client = m.groupdict().get("client")

            if client:
                data[client] = {
                    "source_ip": ip,
                    "last_log_line": line.strip()
                }
                print(f"[SOURCE] client={client} source_ip={ip}")
            else:
                print(f"[CONNECTION] source_ip={ip}")

            save_map(data)
            matched = True
            break

    return matched


print("=" * 70)
print("MQTT SOURCE TRACER")
print("=" * 70)
print(f"Watching: {MOSQUITTO_LOG}")

if not MOSQUITTO_LOG.exists():
    print("[!] Mosquitto log does not exist yet.")
    print("    Start Mosquitto with a config that writes to this file.")
    raise SystemExit(1)

data = load_map()

with MOSQUITTO_LOG.open("r", encoding="utf-8", errors="replace") as f:
    f.seek(0, 2)

    while True:
        line = f.readline()
        if not line:
            time.sleep(0.5)
            continue

        process_line(line, data)
