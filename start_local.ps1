Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  Starting Smart Healthcare Ecosystem (PRJ-02)" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

# 1. Start FastAPI Backend Server
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

# 2. Start Vite React Frontend
Write-Host "[2/2] Starting React + Vite Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev -- --host 127.0.0.1 --port 5173"

Write-Host ""
Write-Host "Services are now running!" -ForegroundColor Yellow
Write-Host "Frontend Web App : http://127.0.0.1:5173" -ForegroundColor White
Write-Host "Backend API      : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Swagger Docs     : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "=========================================================" -ForegroundColor Cyan
Start-Process "http://127.0.0.1:5173"
