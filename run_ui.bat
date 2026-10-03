
### `run_ui.bat`

:::writing{variant="standard" id="74106" title="run_ui.bat"}
@echo off
setlocal

set "DBFILE=..\tests-real-sensitive-data\projects.yaml"
set "APQA_DB_FILE=%DBFILE%"

call run_init.bat
if errorlevel 1 exit /b %errorlevel%

".venv\Scripts\python.exe" apqa_bundle.py --program ui --db-file "%DBFILE%"

if errorlevel 1 exit /b %errorlevel%

endlocal
:::
