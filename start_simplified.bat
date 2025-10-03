@echo off
echo Starting WebIntel Analytics - Simplified Setup
echo =============================================
echo.

echo Starting Python FastAPI Backend (Port 8000)...
start "Python Backend" cmd /k "cd backend && python start_backend.py"

timeout /t 3 /nobreak > nul

echo Starting Angular Frontend (Port 4200)...
start "Angular Frontend" cmd /k "cd angular-frontend && npm start"

echo.
echo Services are starting...
echo.
echo Python Backend: http://localhost:8000
echo Angular Frontend: http://localhost:4200
echo.
echo Open http://localhost:4200 in your browser
echo.
echo Press any key to exit...
pause > nul
