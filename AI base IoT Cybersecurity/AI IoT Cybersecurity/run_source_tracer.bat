@echo off
cd /d "%~dp0"
call iot_security_env\Scripts\activate.bat
python source_tracer.py
pause
