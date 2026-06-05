@echo off
TITLE AI Earnings Call Auditor - Frontend Developer Server
echo --------------------------------------------------
echo Launching React Vite Frontend...
echo --------------------------------------------------
cd %~dp0frontend
if not exist node_modules (
    echo [System] node_modules not found. Installing package assets...
    npm install
)
echo [System] Launching dev server on port 5173...
npm run dev
pause
