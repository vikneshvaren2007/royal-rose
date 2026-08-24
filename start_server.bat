@echo off
title ROYAL ROSE MILK - Backend Server
echo ========================================================
echo   ROYAL ROSE MILK - Starting Python Flask Backend
echo ========================================================
echo.
cd /d "%~dp0"
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Python command failed. Trying with backend/app.py...
    python backend/app.py
)
pause
