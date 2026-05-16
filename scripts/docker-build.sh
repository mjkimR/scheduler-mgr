#!/usr/bin/env bash
set -e

MODULE=$1
TAG=$2

if [ "$MODULE" = "all" ]; then
    for m in $AVAILABLE_MODULES; do
        script="./docker/build_$m.sh"
        if [ -f "$script" ]; then
            echo "Running $script -t $TAG"
            bash "$script" -t "$TAG"
        else
            echo "Warning: Build script $script not found."
        fi
    done
else
    matched=0
    for m in $AVAILABLE_MODULES; do
        if [ "$m" = "$MODULE" ]; then
            matched=1
            break
        fi
    done
    if [ "$matched" -eq 1 ]; then
        script="./docker/build_$MODULE.sh"
        if [ -f "$script" ]; then
            bash "$script" -t "$TAG"
        else
            echo "Error: Build script $script not found."
            exit 1
        fi
    else
        echo "Error: Unknown module '$MODULE'"
        echo "Available modules are: $AVAILABLE_MODULES"
        exit 1
    fi
fi
