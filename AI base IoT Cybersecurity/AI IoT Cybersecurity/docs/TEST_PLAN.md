# Test Plan

## Test A: Normal baseline

python simulator.py --mode normal --device ESP32_01 --count 40 --interval 2

Expected:
- device discovered
- baseline reaches 30/30
- subsequent observations generally NORMAL

## Test B: Rapid burst

python simulator.py --mode burst --device ESP32_01 --count 100 --interval 0.05

Expected:
- message rate rises sharply
- safety rule high_rate may trigger
- ML result may also become anomalous depending on the baseline

## Test C: Large payload + new topic

python simulator.py --mode abnormal --device ESP32_01 --count 20 --interval 0.1

Expected:
- large payload
- new topic
- very short interval
- safety flags should trigger

## Test D: Mixed

python simulator.py --mode mixed --device ESP32_01 --count 30 --interval 0.1

Expected:
- mixture of normal and abnormal telemetry
- anomaly events written to data/anomaly_events.jsonl

Do not treat a test event as proof of a real attack.
