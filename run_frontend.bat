@echo off
echo =======================================================
echo Starting AI Business Operations Agent - Frontend Server
echo UI: http://localhost:5173
echo =======================================================
cd /d "%~dp0frontend"
npm run dev
