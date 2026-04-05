@echo off
setlocal
cd /d "%~dp0"
title Open Vehicle Database - Picker
start "OVDB Picker Server" /MIN cmd /k call "%~dp0install\start-picker-server.cmd"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8080/catalog/"
