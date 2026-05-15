#!/bin/bash
set -ex

# 1) Run DB migrations
alembic upgrade head

# 2) Start FastAPI server
exec gunicorn --bind :$PORT -k uvicorn.workers.UvicornWorker --workers $WORKERS --timeout $TIMEOUT app.main:app
