@echo off
setlocal
set "VBOOK_STATUS_PYTHON=D:\anaconda3\envs\App\python.exe"
if not exist "%VBOOK_STATUS_PYTHON%" set "VBOOK_STATUS_PYTHON=python"
"%VBOOK_STATUS_PYTHON%" "%~dp0production_workflow_status.py" %*
exit /b %errorlevel%
