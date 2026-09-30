@echo off
cd /d "%~dp0"
docker compose up -d
if errorlevel 1 (
  echo Docker Compose failed. Make sure Docker Desktop is installed and running.
  pause
  exit /b 1
)
echo Grafana: http://localhost:3000
echo InfluxDB: http://localhost:8086
echo Grafana login: admin / admin
pause
