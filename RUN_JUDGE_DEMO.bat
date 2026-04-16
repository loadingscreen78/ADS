@echo off
echo ================================================================================
echo                    ML AUTO-RETRAIN SYSTEM
echo                  GPU ACCELERATION DEMONSTRATION
echo                        For Judges Review
echo ================================================================================
echo.
echo This demonstration will show:
echo   1. Real-time drift detection
echo   2. CARA cost-aware decision making
echo   3. Automatic model retraining
echo   4. GPU acceleration (10-50x faster)
echo   5. Cost savings analysis
echo.
echo ================================================================================
echo.

REM Activate conda environment
call D:\miniconda3\Scripts\activate.bat ml_retrain
if errorlevel 1 (
    echo [ERROR] Could not activate conda environment
    pause
    exit /b 1
)

echo [OK] Environment activated
echo.
echo Starting demonstration...
echo.

REM Run demo script
python demo_gpu_retraining.py

echo.
echo ================================================================================
echo                    DEMONSTRATION COMPLETE!
echo ================================================================================
echo.
echo Next steps:
echo   1. Open dashboard: http://localhost:8080
echo   2. Show judges the real-time monitoring
echo   3. Process batches to show drift detection
echo   4. Explain LSTM innovation (2-week prediction)
echo   5. Show fairness monitoring
echo.
echo For detailed script, see: 🎬_JUDGE_DEMONSTRATION_SCRIPT.md
echo.
pause
