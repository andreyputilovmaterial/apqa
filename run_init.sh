#!/usr/bin/env bash
set -e




echo "Prep python"
echo "set venv"
if [ -x ".venv/Scripts/python.exe" ]; then
    pythonexecutable=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
    pythonexecutable=".venv/bin/python"
else
    python -m venv .venv
    if [ -x ".venv/Scripts/python.exe" ]; then
        pythonexecutable=".venv/Scripts/python.exe"
    elif [ -x ".venv/bin/python" ]; then
        pythonexecutable=".venv/bin/python"
    else
        python -m venv .venv
        echo "No Python virtual environment found"
        exit 1
    fi
fi
echo "Upd dependencies"
"$pythonexecutable" -m pip install -r requirements.txt
echo "done"
echo -
echo -



# Install optional per-cmdlet/per-processor dependencies (best-effort).
# A missing optional dependency must not fail the whole init: the affected
# cmdlets are imported as "unavailable" and only raise their import error when
# actually used. The distributed copy scans optional_dependencies/ instead.
if [ -d src/cmdlets ]; then
    for requirements in $(find src/cmdlets -type f -name 'requirements.txt' | sort); do
        echo "installing optional dependencies: $requirements"
        if ! "$pythonexecutable" -m pip install -r "$requirements"; then
            echo "WARNING: optional dependencies in $requirements not installed (the corresponding cmdlets will be unavailable)"
        fi
    done
fi


"$pythonexecutable" -m src.launcher --program done
