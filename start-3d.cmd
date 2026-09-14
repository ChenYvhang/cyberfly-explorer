@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" server3d.py
if errorlevel 1 pause
