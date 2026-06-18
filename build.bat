@ECHO OFF

ECHO Clear up dist\...
IF EXIST dist (
    REM -
) ELSE (
    MKDIR dist
)
DEL /F /Q dist\*

ECHO -
ECHO -
ECHO Update program version
ECHO '''For auto-generated files''' > src\GENERATED\__init__.py
ECHO # THIS IS AUTO-GENERATED > src\GENERATED\_VERSION.py
python -c "from datetime import datetime; print(f'# {datetime.now()}')" >> src\GENERATED\_VERSION.py
ECHO _VERSION = ''' >> src\GENERATED\_VERSION.py
git describe --tags --dirty >> src\GENERATED\_VERSION.py
ECHO ''' >> src\GENERATED\_VERSION.py
ECHO Done


ECHO -
ECHO -
ECHO Produce distributable .py bundle - calling pinliner...
REM REM :: comment: please delete .pyc files before every call of the mdmqaap_bundle - this is implemented in my fork of the pinliner
@REM python src_dev_build\lib\pinliner\pinliner\pinliner.py src -o dist/mdmqaap_bundle.py --verbose
python src_dev_build\lib\pinliner\pinliner\pinliner.py src -o dist/mdmqaap_bundle.py
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
ECHO Done

ECHO -
ECHO -
ECHO Patching mdmqaap_bundle.py...
ECHO # ... >> dist/mdmqaap_bundle.py
ECHO # print('within mdmqaap_bundle') >> dist/mdmqaap_bundle.py
REM REM :: no need for this, the root package is loaded automatically
@REM ECHO # import mdmqaap_bundle >> dist/mdmqaap_bundle.py
ECHO from src import launcher >> dist/mdmqaap_bundle.py
ECHO launcher.main() >> dist/mdmqaap_bundle.py
ECHO # print('out of mdmqaap_bundle') >> dist/mdmqaap_bundle.py
ECHO Done


@REM DEL *.pyc
@REM IF EXIST __pycache__ (
@REM DEL /F /Q __pycache__\*
@REM )
@REM IF EXIST __pycache__ (
@REM RMDIR /Q /S __pycache__
@REM )

@REM ECHO Out

@REM ECHO -
@REM ECHO -
@REM ECHO Bring a copy to ./tests-real-sensitive-data/ folder
@REM COPY .\dist\mdmqaap_bundle.py .\tests-real-sensitive-data\current\ 2>nul
@REM IF errorlevel 1 (
@REM     REM :: That's ok to continue, just need to print a message that "not copied"
@REM     ECHO Not updated
@REM )

ECHO -
ECHO -
ECHO All done, the end

