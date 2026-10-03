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



# echo "Discover optional dependencies for textconv processors"
# #optional_dependencies=$(find src/textconv/processors -type f -path '*/requirements.txt' -print0)
# optional_dependencies=$(find src/textconv/processors -type f -path '*/requirements.txt' -print)
# echo "done"
# echo -
# echo -



# echo "Install optional dependencies for textconv processors"
# # printf '%s' "$optional_dependencies" |
# # while IFS= read -r -d '' requirements; do
# while IFS= read -r requirements; do
#     echo "installing for $requirements:"
#     if ! "$pythonexecutable" -m pip install -r "$requirements"; then
#         echo "WARNING: not installed"
#     fi
# done <<< "$optional_dependencies"
# echo "done"
# echo -
# echo -


"$pythonexecutable" "apqa_bundle.py" --program done
