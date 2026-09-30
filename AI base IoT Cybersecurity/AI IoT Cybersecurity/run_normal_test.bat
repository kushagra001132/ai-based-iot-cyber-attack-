@echo off
cd /d "%~dp0"
call iot_security_env\Scripts\activate.bat
python simulator.py --mode normal --device ESP32_01 --count 40 --interval 2
pause
