@echo off
title AERO // J.A.R.V.I.S.
cd /d "%~dp0"
echo ============================================================
echo   AERO // J.A.R.V.I.S. LAUNCHER
echo ============================================================
echo.

set PYTHON_BIN=python
if exist .venv\Scripts\python.exe (
    echo [AERO] Using virtual environment Python...
    set PYTHON_BIN=.venv\Scripts\python.exe
) else (
    echo [AERO] Using system Python...
)

echo Starting AERO server with llama3...
echo.
%PYTHON_BIN% gui.py --model llama3
pause
