@echo off
echo Installing WebIntel Analytics Dependencies
echo =========================================
echo.

echo Installing Angular Frontend Dependencies...
cd angular-frontend
call npm install
if %errorlevel% neq 0 (
    echo Error installing Angular dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Ensure Python backend dependencies are installed (pip install -r backend/requirements.txt)
echo 2. Run start_simplified.bat to start both services
echo 3. Open http://localhost:4200 in your browser
echo.
pause
