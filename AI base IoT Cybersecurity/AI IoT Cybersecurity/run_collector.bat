@echo off
cd /d "%~dp0"
call iot_security_env\Scripts\activate.bat
python collector.py
pause
