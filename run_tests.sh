#!/usr/bin/env bash
set -e

DBFILE="tests-real-sensitive-data/projects.yaml"
# export APQA_DB_FILE="$DBFILE"

./run_init.sh

APQA_DB_FILE="$DBFILE" ./.venv/bin/python -m pytest --import-mode=importlib  apqa_bundle.py

