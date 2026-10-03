@echo off
setlocal

echo Prep python
echo set venv

if exist ".venv\Scripts\python.exe" (
set "pythonexecutable=.venv\Scripts\python.exe"
) else (
echo Creating Python virtual environment...
python -m venv .venv

if exist ".venv\Scripts\python.exe" (
    set "pythonexecutable=.venv\Scripts\python.exe"
) else (
    echo No Python virtual environment found
    exit /b 1
)


)

echo Upd dependencies
"%pythonexecutable%" -m pip install -r requirements.txt

echo done
echo.
echo.

"%pythonexecutable%" apqa_bundle.py --program done

if errorlevel 1 exit /b %errorlevel%

endlocal