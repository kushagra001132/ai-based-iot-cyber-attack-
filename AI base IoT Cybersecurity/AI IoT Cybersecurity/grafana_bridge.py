from __future__ import annotations
import json, os, time
from pathlib import Path
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
TELEMETRY = DATA / 'telemetry.jsonl'
ANOMALIES = DATA / 'anomaly_events.jsonl'
INFLUX_URL = os.getenv('INFLUX_URL', 'http://127.0.0.1:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'iot-security-local-token-change-me')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'iot_security')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'iot_security')

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def event_time(obj):
    for k in ('time','timestamp','ts'):
        if obj.get(k):
            try: return datetime.fromisoformat(str(obj[k]).replace('Z','+00:00'))
            except ValueError: pass
    return datetime.now(timezone.utc)

def payload_fields(obj):
    raw = obj.get('payload_preview')
    if not isinstance(raw, str): return {}
    try:
        x = json.loads(raw); return x if isinstance(x, dict) else {}
    except Exception: return {}

def write_record(api, obj, measurement):
    device = str(obj.get('device','unknown')); topic = str(obj.get('topic','unknown'))
    p = Point(measurement).tag('device', device).tag('topic', topic)
    features = obj.get('features')
    if isinstance(features, list) and len(features) >= 4:
        for k,v in zip(('message_rate','average_size','topic_count','average_interval'), features[:4]):
            v=num(v)
            if v is not None: p=p.field(k,v)
    for k in ('size','ai_score','messages'):
        v=num(obj.get(k))
        if v is not None: p=p.field(k,v)
    payload = payload_fields(obj)
    for k in ('temperature','distance','humidity','pressure','uptime'):
        v=num(payload.get(k))
        if v is not None: p=p.field(k,v)
    for k in ('status','lock','door','reason','note'):
        v=obj.get(k, payload.get(k))
        if v is not None: p=p.field(k,str(v))
    p=p.time(event_time(obj), WritePrecision.NS)
    api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)

def tail(path, api, measurement, pos):
    if not path.exists(): return pos
    if path.stat().st_size < pos: pos=0
    with path.open('r',encoding='utf-8',errors='replace') as f:
        f.seek(pos)
        for line in f:
            line=line.strip()
            if not line: continue
            try: write_record(api,json.loads(line),measurement)
            except Exception as e: print(f'[bridge] skipped {path.name}: {e}')
        return f.tell()

def main():
    DATA.mkdir(exist_ok=True)
    client=InfluxDBClient(url=INFLUX_URL,token=INFLUX_TOKEN,org=INFLUX_ORG)
    api=client.write_api(write_options=SYNCHRONOUS)
    pos={TELEMETRY:0,ANOMALIES:0}
    print('[bridge] InfluxDB:',INFLUX_URL)
    print('[bridge] Watching telemetry.jsonl and anomaly_events.jsonl')
    try:
        while True:
            pos[TELEMETRY]=tail(TELEMETRY,api,'iot_telemetry',pos[TELEMETRY])
            pos[ANOMALIES]=tail(ANOMALIES,api,'security_anomaly',pos[ANOMALIES])
            time.sleep(1)
    except KeyboardInterrupt: print('\n[bridge] Stopping...')
    finally:
        api.close(); client.close()

if __name__=='__main__': main()
