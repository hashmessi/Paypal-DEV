@echo off
cls
echo =====================================================================
echo  PROMISELOOP: AUTONOMOUS LIVE DEMO DIRECTOR
echo  Target: https://promiseloop-web.onrender.com/ (Production Render)
echo =====================================================================
echo.
echo Starting Google Chrome in headed mode on your desktop...
python -u scripts\live_demo_driver.py
echo.
echo Demo run completed.
pause

