#!/usr/bin/env bash

set -e

echo "Starting AutoInspect RQ worker..."

python -m backend.app.worker.run_worker &

echo "Starting AutoInspect FastAPI server..."

exec uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT"