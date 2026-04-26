@echo off
title SENTINEL SIEM - Setup
color 0B
cls

echo.
echo  ============================================================
echo    SENTINEL SIEM  ^|  One-Click Setup
echo    Engineered by Abhay Singh Taknet
echo  ============================================================
echo.

:: ── Step 1: Python check ─────────────────────────────────────
echo  [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python not found on this system.
    echo.
    echo  Please download and install Python 3.10 or above from:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During install, check the box that says
    echo  "Add Python to PATH" before clicking Install Now.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER% detected.
echo.

:: ── Step 2: pip check ────────────────────────────────────────
echo  [2/7] Checking pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [INFO] pip not found. Installing...
    python -m ensurepip --upgrade
)
echo  [OK] pip is available.
echo.

:: ── Step 3: Upgrade pip ──────────────────────────────────────
echo  [3/7] Upgrading pip to latest version...
python -m pip install --upgrade pip --quiet
echo  [OK] pip upgraded.
echo.

:: ── Step 4: Install all project dependencies ─────────────────
echo  [4/7] Installing required packages...
echo        This may take 1-3 minutes on first run.
echo.
echo        Packages: Flask, scikit-learn, pandas, numpy,
echo                  psutil, requests, Werkzeug
echo.
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Some packages failed to install.
    echo.
    echo  Possible reasons:
    echo    - No internet connection
    echo    - Antivirus blocking pip
    echo    - Python version too old (need 3.10+)
    echo.
    echo  Try running this command manually:
    echo  python -m pip install flask scikit-learn pandas numpy psutil requests
    echo.
    pause
    exit /b 1
)
echo.
echo  [OK] All packages installed.
echo.

:: ── Step 5: Verify each critical package ─────────────────────
echo  [5/7] Verifying installations...
echo.

python -c "import flask; print('  [OK] Flask', flask.__version__)"
if %errorlevel% neq 0 (
    echo  [FAIL] Flask — retrying...
    python -m pip install flask --quiet
)

python -c "import sklearn; print('  [OK] scikit-learn', sklearn.__version__)"
if %errorlevel% neq 0 (
    echo  [FAIL] scikit-learn — retrying...
    python -m pip install scikit-learn --quiet
)

python -c "import pandas; print('  [OK] pandas', pandas.__version__)"
if %errorlevel% neq 0 (
    echo  [FAIL] pandas — retrying...
    python -m pip install pandas --quiet
)

python -c "import numpy; print('  [OK] numpy', numpy.__version__)"
if %errorlevel% neq 0 (
    echo  [FAIL] numpy — retrying...
    python -m pip install numpy --quiet
)

python -c "import psutil; print('  [OK] psutil', psutil.__version__)"
if %errorlevel% neq 0 (
    echo  [FAIL] psutil — retrying...
    python -m pip install psutil --quiet
)

python -c "import requests; print('  [OK] requests', requests.__version__)"
if %errorlevel% neq 0 (
    echo  [FAIL] requests — retrying...
    python -m pip install requests --quiet
)
echo.

:: ── Step 6: Create required folders ──────────────────────────
echo  [6/7] Creating project directories...
if not exist "logs"         mkdir logs
if not exist "db"           mkdir db
if not exist "secure_data"  mkdir secure_data
if not exist "exports"      mkdir exports
if not exist "static"       mkdir static

if not exist "logs\banned_ips.json"    echo {} > logs\banned_ips.json
if not exist "logs\safe_logs.txt"      type nul > logs\safe_logs.txt
if not exist "logs\threat_events.txt"  type nul > logs\threat_events.txt

if not exist "secure_data\company_secrets.txt" (
    echo PROJECT SENTINEL — CLASSIFIED VAULT > secure_data\company_secrets.txt
    echo. >> secure_data\company_secrets.txt
    echo API_KEY      : SENTINEL-9921 >> secure_data\company_secrets.txt
    echo DB_PASSWORD  : s3cur3_v4ult_2024 >> secure_data\company_secrets.txt
    echo ADMIN_TOKEN  : eyJhbGciOiJIUzI1NiJ9.sentinel >> secure_data\company_secrets.txt
    echo INTERNAL_IP  : 192.168.1.100 >> secure_data\company_secrets.txt
)
echo  [OK] Directories and default files created.
echo.

:: ── Step 7: Final verification ───────────────────────────────
echo  [7/7] Running final system check...
python -c "import flask, sklearn, pandas, numpy, psutil, requests; print('  [OK] All 6 modules verified and ready.')"
if %errorlevel% neq 0 (
    echo.
    echo  [WARN] One or more modules may have issues.
    echo  Try closing this window and running setup.bat again.
    echo.
    pause
    exit /b 1
)
echo.

echo  ============================================================
echo.
echo    SETUP COMPLETE!
echo.
echo    All dependencies installed. To start the project:
echo.
echo      1. Double-click  run.bat
echo      2. Press  [1]  to Start SENTINEL SIEM
echo      3. Dashboard opens at  http://localhost:5000
echo.
echo  ============================================================
echo.
pause
