@echo off
REM ========================================================================
REM Conda Environment Setup for ML Auto-Retrain System
REM ========================================================================

echo.
echo ======================================================================
echo CREATING CONDA ENVIRONMENT
echo ======================================================================
echo.

REM Create conda environment with Python 3.10
echo [1/4] Creating conda environment 'ml_retrain'...
call conda create -n ml_retrain python=3.10 -y

echo.
echo [2/4] Installing core dependencies...
call conda install -n ml_retrain -c conda-forge numpy pandas scikit-learn scipy -y

echo.
echo [3/4] Installing additional packages with pip...
call conda run -n ml_retrain pip install tensorflow==2.15.0 mlflow==2.19.0 fastapi==0.115.0 uvicorn==0.34.0 pyarrow==18.0.0 joblib==1.4.2 python-dotenv==1.0.1 kaggle==1.6.6

echo.
echo [4/4] Environment setup complete!
echo.
echo ======================================================================
echo To activate the environment, run:
echo     conda activate ml_retrain
echo.
echo To run the implementation:
echo     conda run -n ml_retrain python run_day1_to_day6.py
echo ======================================================================
echo.
pause
