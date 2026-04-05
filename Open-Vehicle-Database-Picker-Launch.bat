@echo off
setlocal
cd /d "%~dp0"
set "OVDB_URL=http://127.0.0.1:8080/catalog/"

title Open Vehicle Database - Picker
start "OVDB Picker Server" /MIN cmd /k call "%~dp0install\start-picker-server.cmd"
timeout /t 2 /nobreak >nul

rem Chromium: --start-fullscreen = F11-style fullscreen (not just maximized)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --start-fullscreen "%OVDB_URL%"
  goto :eof
)
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --start-fullscreen "%OVDB_URL%"
  goto :eof
)
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
  start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" --start-fullscreen "%OVDB_URL%"
  goto :eof
)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --start-fullscreen "%OVDB_URL%"
  goto :eof
)

rem Default browser: cannot force fullscreen from a .bat
start "" "%OVDB_URL%"
