@echo off
echo ================================================================================
echo                    ML AUTO-RETRAIN DASHBOARD LAUNCHER
echo ================================================================================
echo.
echo Starting the dashboard server...
echo.

REM Try to activate conda environment and run
call D:\miniconda3\Scripts\activate.bat ml_retrain
if errorlevel 1 (
    echo [ERROR] Could not activate conda environment
    pause
    exit /b 1
)

echo [OK] Conda environment activated
echo.
echo Starting API server on http://localhost:8080
echo Opening browser in 3 seconds...
echo.
echo Press Ctrl+C to stop the server
echo ================================================================================
echo.

python run_dashboard.py

pause
