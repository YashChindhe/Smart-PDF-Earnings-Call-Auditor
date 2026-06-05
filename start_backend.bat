@echo off
TITLE AI Earnings Call Auditor - Backend Server
echo --------------------------------------------------
echo Launching FastAPI Backend...
echo --------------------------------------------------
cd %~dp0backend
if not exist venv (
    echo [System] Virtual environment not found. Creating venv...
    python -m venv venv
    echo [System] Installing dependencies...
    venv\Scripts\pip install -r requirements.txt
)
echo [System] Starting Uvicorn API server on port 7860...
venv\Scripts\uvicorn main:app --port 7860 --reload
pause
