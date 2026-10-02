@echo off
echo =======================================================
echo Seeding AI Business Operations Database...
echo =======================================================
cd /d "%~dp0"
set PYTHONPATH=backend
.\.venv\Scripts\python.exe -m app.db.seed
pause
