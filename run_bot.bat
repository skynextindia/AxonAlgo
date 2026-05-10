@echo off
title AxonAlgo VPS Watchdog
:loop
echo [%date% %time%] Starting AxonAlgo Trading Bot...
python main.py
echo [%date% %time%] Bot crashed or stopped. Restarting in 10 seconds...
timeout /t 10
goto loop
