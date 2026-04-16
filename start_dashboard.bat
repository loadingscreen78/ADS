@echo off
echo ================================================================================
echo                    ML AUTO-RETRAIN DASHBOARD
echo                         Starting System
echo ================================================================================
echo.

echo [1/3] Starting API Server...
start "ML API Server" cmd /k "conda activate ml_retrain && python src/services/api_server.py"

timeout /t 3 /nobreak >nul

echo [2/3] Opening Dashboard in Browser...
start http://localhost:8000

echo [3/3] System Started!
echo.
echo ================================================================================
echo Dashboard is now running!
echo.
echo API Server: http://localhost:8000
echo Dashboard:  http://localhost:8000 (opens automatically)
echo.
echo Press Ctrl+C in the API Server window to stop
echo ================================================================================
echo.
pause