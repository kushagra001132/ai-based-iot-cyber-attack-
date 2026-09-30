import argparse
import json
import random
import time

from paho.mqtt import client as mqtt

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["normal", "burst", "abnormal", "mixed"], default="normal")
parser.add_argument("--device", default="ESP32_01")
parser.add_argument("--count", type=int, default=30)
parser.add_argument("--interval", type=float, default=2.0)
parser.add_argument("--broker", default="127.0.0.1")
parser.add_argument("--port", type=int, default=1883)
args = parser.parse_args()

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"SIM_{args.device}"
)
client.connect(args.broker, args.port, 60)
client.loop_start()

try:
    for i in range(args.count):
        if args.mode == "normal":
            topic = f"iot/{args.device}/telemetry"
            payload = {
                "device": args.device,
                "temperature": round(random.uniform(25, 32), 2),
                "status": "normal",
                "seq": i
            }

        elif args.mode == "burst":
            topic = f"iot/{args.device}/telemetry"
            payload = {
                "device": args.device,
                "temperature": 28,
                "status": "normal",
                "test": "rapid_burst",
                "seq": i
            }

        elif args.mode == "abnormal":
            topic = f"iot/{args.device}/attack_test"
            payload = {
                "device": args.device,
                "temperature": 999,
                "status": "ATTACK_TEST",
                "seq": i,
                "data": "X" * 5000
            }

        else:  # mixed
            if i % 3 == 0:
                topic = f"iot/{args.device}/attack_test"
                payload = {
                    "device": args.device,
                    "temperature": 999,
                    "status": "ATTACK_TEST",
                    "seq": i,
                    "data": "X" * 5000
                }
            else:
                topic = f"iot/{args.device}/telemetry"
                payload = {
                    "device": args.device,
                    "temperature": 28,
                    "status": "normal",
                    "seq": i
                }

        data = json.dumps(payload, separators=(",", ":"))
        client.publish(topic, data, qos=0)
        print(f"[{i+1}/{args.count}] {topic} {len(data)} bytes")
        time.sleep(args.interval)

finally:
    client.loop_stop()
    client.disconnect()
