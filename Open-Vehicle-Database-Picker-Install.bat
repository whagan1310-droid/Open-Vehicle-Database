@echo off
setlocal
cd /d "%~dp0"
title Open Vehicle Database - Picker Installer
echo.
echo  Open Vehicle Database - Picker
echo  This window will install Python and Node.js if needed, then open the catalog.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install\install-picker.ps1"
if errorlevel 1 (
  echo.
  echo Install step failed. See messages above.
  pause
  exit /b 1
)
echo.
pause
