@echo off
setlocal

set "DBFILE=..\tests-real-sensitive-data\projects.yaml"
set "APQA_DB_FILE=%DBFILE%"

call run_init.bat
if errorlevel 1 exit /b %errorlevel%

".venv\Scripts\python.exe" -m pytest --import-mode=importlib apqa_bundle.py

if errorlevel 1 exit /b %errorlevel%

endlocal