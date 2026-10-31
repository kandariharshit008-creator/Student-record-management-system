@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" launch_app.py
) else (
  python launch_app.py
)
if errorlevel 1 (
  echo.
  echo The app could not start. Install Python dependencies with:
  echo python -m pip install -r requirements.txt
  pause
)
