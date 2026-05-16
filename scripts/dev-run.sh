#!/usr/bin/env bash
set -e

MODULE=$1

case "$MODULE" in
    hub)
        cd modules/hub && uv run uvicorn app.main:create_app --port 8389 --reload
        ;;
    *)
        echo "Error: Unknown module '$MODULE'"
        echo "Available modules are: $AVAILABLE_MODULES"
        exit 1
        ;;
esac
