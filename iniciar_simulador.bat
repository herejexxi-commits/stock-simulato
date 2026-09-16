@echo off
echo ==============================================
echo Iniciando Simulador de Acciones...
echo ==============================================

:: Iniciar el backend minimizado
start /min "Backend - Stock Simulator" cmd /c "cd backend && call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Esperar un momento para que el backend inicie
timeout /t 3 /nobreak >nul

:: Iniciar el frontend minimizado
start /min "Frontend - Stock Simulator" cmd /c "cd frontend && npm run dev"

:: Esperar un par de segundos para abrir el navegador
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo ==============================================
echo Simulador iniciado (ventanas minimizadas en la barra de tareas). 
echo Para apagarlo, simplemente cierra esas ventanas negras.
echo ==============================================
pause
