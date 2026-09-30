@echo off
cd /d "%~dp0"
call iot_security_env\Scripts\activate.bat
python simulator.py --mode abnormal --device ESP32_01 --count 20 --interval 0.1
pause
