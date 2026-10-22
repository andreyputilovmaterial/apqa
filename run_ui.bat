
@echo off
setlocal

@REM  set "DBFILE=tests-real-sensitive-data\projects.yaml"
set "DBFILE=tests-real-sensitive-data\projects.sqlite3"
set "APQA_DB_FILE=%DBFILE%"

call run_init.bat
if errorlevel 1 exit /b %errorlevel%

".venv\Scripts\python.exe" -m src.launcher --program ui --db-file "%DBFILE%"

if errorlevel 1 exit /b %errorlevel%

endlocal
:::
