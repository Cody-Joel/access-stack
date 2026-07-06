@echo off
setlocal
cd /d "C:\Op\Op"

REM --- Optional: add the tiny firewall rules (needs admin ONCE) ---
if "%1"=="--fw" goto :FW

REM --- Normal run, no elevation needed ---
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Op-Lite.ps1"
exit /b %errorlevel%

:FW
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','%~dp0Add-FwRules.ps1'"
exit /b