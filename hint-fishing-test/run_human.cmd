@echo off
REM Windows: run "run_human.cmd P01" in Command Prompt / PowerShell.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_human.ps1" %*
if errorlevel 1 pause
