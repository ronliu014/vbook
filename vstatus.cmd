@echo off
call "%~dp0tools\production_workflow_status.cmd" %*
exit /b %errorlevel%
