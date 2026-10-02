@echo off
echo =======================================================
echo Starting AI Business Operations Agent - Backend Server
echo API Docs: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo =======================================================
cd /d "%~dp0"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
