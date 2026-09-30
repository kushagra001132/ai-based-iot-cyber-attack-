@echo off
cd /d "%~dp0"
python -m pip install -r grafana_requirements.txt
python grafana_bridge.py
pause
