@echo off
setlocal
cd /d "%~dp0"
set "OVDB_URL=http://127.0.0.1:8080/catalog/"

title Open Vehicle Database - Picker
start "OVDB Picker Server" /MIN cmd /k call "%~dp0install\start-picker-server.cmd"
timeout /t 2 /nobreak >nul

rem Fullscreen via PowerShell: temp profile + --new-window avoids Chromium ignoring --start-fullscreen when the browser is already open.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install\open-picker-fullscreen.ps1" "%OVDB_URL%"
