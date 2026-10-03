#!/usr/bin/env bash
set -e

DBFILE="tests-real-sensitive-data/projects.yaml"
# export APQA_DB_FILE="$DBFILE"

./run_init.sh

./.venv/bin/python apqa_bundle.py --program ui --db-file "$DBFILE"

