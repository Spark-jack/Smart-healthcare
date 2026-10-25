@echo off
title Smart Healthcare Platform Launcher
echo =========================================================
echo   Starting Smart Healthcare Ecosystem (PRJ-02)
echo =========================================================
echo.

:: 1. Start FastAPI Backend Server
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "SmartHealth-Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 2. Start Vite React Frontend
echo [2/2] Starting React + Vite Frontend on http://127.0.0.1:5173 ...
start "SmartHealth-Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo =========================================================
echo   Both services are starting!
echo   Frontend Web App:  http://127.0.0.1:5173
echo   Backend REST API:  http://127.0.0.1:8000
echo   Swagger Docs:      http://127.0.0.1:8000/docs
echo =========================================================
echo.
pause
