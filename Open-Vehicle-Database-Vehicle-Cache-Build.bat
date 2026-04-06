@echo off
setlocal
cd /d "%~dp0"
title Open Vehicle Database — Vehicle cache scan
set PYTHONUNBUFFERED=1

echo.
echo  Vehicle cache: lemon-manuals.la  (merge mode — skips pairs already in JSON)
echo  Output: catalog\charm-vehicle-cache.json
echo  Leave this window open. Progress prints below. Ctrl+C saves partial; run this again to resume.
echo.
python scripts/build_charm_vehicle_cache.py --scope coverage --sleep 0.2
echo.
echo  Finished with exit code %ERRORLEVEL%
pause
