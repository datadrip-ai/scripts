@echo off
:: Script to elevate shell permissions in console
:: Check for administrative privileges
net session >nul 2>&1
if %errorlevel% == 0 (
    :: Already running as admin, launch PowerShell
    echo Launching PowerShell as Administrator...
    powershell -NoExit -Command "Set-Location '%CD%'"
    exit /b
) else (
    :: Not running as admin, relaunch with elevation
    echo Requesting administrative privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %CD% && powershell -NoExit' -Verb RunAs"
    exit /b
)