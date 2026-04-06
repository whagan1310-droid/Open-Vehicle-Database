@echo off
setlocal
cd /d "%~dp0"
set "OVDB_URL=http://127.0.0.1:8080/catalog/"

title Open Vehicle Database - Picker
start "OVDB Picker Server" /MIN cmd /k call "%~dp0install\start-picker-server.cmd"
timeout /t 2 /nobreak >nul

rem Fullscreen or windowed: open-picker-catalog.ps1 checks for PICKER_VARIANT_Windows.txt (Windows release ZIP only).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install\open-picker-catalog.ps1" -Url "%OVDB_URL%"
