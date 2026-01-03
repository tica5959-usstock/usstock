@echo off
echo Starting US Stock Dashboard...
echo Layout: Flask Web Server (Port 5001)

cd /d %~dp0

:: Check if virtual environment exists (optional but good practice)
:: For now, assuming Global or User Python is used as per user environment
echo Installing missing dependencies...
pip install -r requirements.txt > nul 2>&1

echo Starting Flask Application...
python flask_app.py

pause
