@echo off
REM ========================================================================
REM Day 1-6 Implementation Setup and Run Script
REM ========================================================================

echo.
echo ======================================================================
echo ML AUTO-RETRAIN SYSTEM - SETUP AND RUN
echo ======================================================================
echo.

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Conda detected - using conda environment
    goto :CONDA_SETUP
) else (
    echo [INFO] Conda not found - using standard Python
    goto :PYTHON_SETUP
)

:CONDA_SETUP
echo.
echo [Step 1] Creating conda environment 'ml_retrain'...
call conda create -n ml_retrain python=3.10 -y

echo.
echo [Step 2] Installing dependencies...
call conda run -n ml_retrain pip install -r requirements.txt

echo.
echo [Step 3] Running verification...
call conda run -n ml_retrain python verify_implementation.py

echo.
echo [Step 4] Running complete Day 1-6 workflow...
call conda run -n ml_retrain python run_day1_to_day6.py

goto :END

:PYTHON_SETUP
echo.
echo [Step 1] Creating virtual environment...
python -m venv venv

echo.
echo [Step 2] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [Step 3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [Step 4] Running verification...
python verify_implementation.py

echo.
echo [Step 5] Running complete Day 1-6 workflow...
python run_day1_to_day6.py

:END
echo.
echo ======================================================================
echo COMPLETE!
echo ======================================================================
echo.
pause
