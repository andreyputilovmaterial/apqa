@echo off
setlocal

@REM  set "DBFILE=tests-real-sensitive-data\projects.yaml"
set "DBFILE=tests-real-sensitive-data\projects.sqlite3"
set "APQA_DB_FILE=%DBFILE%"

call run_init.bat
if errorlevel 1 exit /b %errorlevel%

@REM BEGIN BUILD-ONLY
@REM Build the bundle first (this block is stripped when build.sh copies this file into dist/).
bash build.sh
if errorlevel 1 exit /b %errorlevel%
@REM END BUILD-ONLY
".venv\Scripts\python.exe" -m pytest --import-mode=importlib dist\apqa_bundle.py

if errorlevel 1 exit /b %errorlevel%

endlocal