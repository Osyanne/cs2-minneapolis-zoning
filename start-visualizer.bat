@echo off
chcp 65001 >nul
title CS2 Mineapolis - Visualizador de Zonificacion

cd /d "%~dp0visualizer"

REM Verificar si el puerto 8080 ya esta en uso
netstat -an | findstr ":8080" | findstr "LISTENING" >nul 2>&1
if %errorlevel% == 0 (
    echo.
    echo  [INFO] Servidor ya activo en puerto 8080.
    echo.
) else (
    echo.
    echo  [INFO] Iniciando servidor HTTP en puerto 8080...
    echo  [INFO] Sirviendo desde: %CD%
    echo.
    start "CS2 Mineapolis Server" /MIN cmd /k python -m http.server 8080
    timeout /t 2 /nobreak >nul
)

echo  [INFO] Abriendo http://localhost:8080 en el navegador...
echo.
start "" http://localhost:8080

echo  Listo. Esta ventana se cerrara en 5 segundos.
echo  El servidor sigue corriendo en una ventana minimizada.
echo  Cierra esa ventana para detener el servidor.
timeout /t 5 /nobreak >nul
