#!/usr/bin/env bash
set -e

# DBFILE="tests-real-sensitive-data/projects.yaml"
DBFILE="tests-real-sensitive-data/projects.sqlite3"
# export APQA_DB_FILE="$DBFILE"

./run_init.sh

# BEGIN BUILD-ONLY
# Build the bundle first (this block is stripped when build.sh copies this file into dist/).
./build.sh
# END BUILD-ONLY
APQA_DB_FILE="$DBFILE" ./.venv/bin/python -m pytest --import-mode=importlib dist/apqa_bundle.py

