@echo off
cd /d "%~dp0"
python kiosk_server.py
if errorlevel 1 py -3 kiosk_server.py
pause
