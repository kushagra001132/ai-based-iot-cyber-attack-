import os
import requests

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")


def send_pushover(message, title="IoT Cybersecurity Alert"):
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        print("[!] Pushover credentials not configured")
        return False

    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "title": title,
                "message": message,
            },
            timeout=10,
        )

        if response.status_code == 200:
            print("[+] Pushover notification sent")
            return True

        print(f"[!] Pushover failed: HTTP {response.status_code}")
        return False

    except Exception as e:
        print(f"[!] Pushover error: {e}")
        return False