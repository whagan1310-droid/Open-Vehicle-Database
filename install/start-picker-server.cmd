@echo off
setlocal
cd /d "%~dp0.."
title Open Vehicle Database - Picker Server
echo.
echo  Open Vehicle Database - Picker
echo  Catalog: http://127.0.0.1:8080/catalog/
echo  Close this window to stop the server.
echo.
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
  py -3 -m http.server 8080 -b 127.0.0.1
  goto :done
)
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
  python -m http.server 8080 -b 127.0.0.1
  goto :done
)
where python3 >nul 2>&1
if %ERRORLEVEL% equ 0 (
  python3 -m http.server 8080 -b 127.0.0.1
  goto :done
)
echo ERROR: Python was not found on PATH. Run Open-Vehicle-Database-Picker-Install.bat again.
:done
pause
