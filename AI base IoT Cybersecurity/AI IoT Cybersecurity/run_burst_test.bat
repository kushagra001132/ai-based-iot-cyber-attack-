@echo off
cd /d "%~dp0"
call iot_security_env\Scripts\activate.bat
python simulator.py --mode burst --device ESP32_01 --count 100 --interval 0.05
pause
