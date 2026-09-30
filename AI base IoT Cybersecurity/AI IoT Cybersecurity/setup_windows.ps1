# Run from PowerShell in this folder.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
py -m venv iot_security_env
.\iot_security_env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Write-Host ""
Write-Host "Setup complete. Next: start Mosquitto, collector.py and source_tracer.py."
