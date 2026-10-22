#!/usr/bin/env bash
set -e

# DBFILE="tests-real-sensitive-data/projects.yaml"
DBFILE="tests-real-sensitive-data/projects.sqlite3"
# export APQA_DB_FILE="$DBFILE"

./run_init.sh

./.venv/bin/python -m src.launcher --program ui --db-file "$DBFILE"

