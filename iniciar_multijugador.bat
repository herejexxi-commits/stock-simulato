@echo off
echo ==============================================
echo Iniciando Simulador en Modo Multijugador...
echo ==============================================

:: Iniciar el backend minimizado
start /min "Backend - Stock Simulator" cmd /c "cd backend && call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Esperar un momento para que el backend inicie
timeout /t 3 /nobreak >nul

:: Iniciar el frontend minimizado
start /min "Frontend - Stock Simulator" cmd /c "cd frontend && npm run dev"

:: Esperar un par de segundos para que el frontend inicie
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo ==============================================
echo Abriendo Tunel Seguro hacia Internet...
echo ==============================================
echo Por favor espera unos segundos...
echo A continuacion aparecera un enlace publico (ej: https://tupalabra.loca.lt).
echo Copia ESE ENLACE y enviaselo a tu amigo.
echo.
echo IMPORTANTE: Cuando tu amigo abra el enlace, es posible que la pagina
echo le pida hacer clic en un boton azul que dice "Click to Continue" 
echo por medidas de seguridad.
echo ==============================================
echo.
cmd /c "npx --yes localtunnel --port 5173"

pause
