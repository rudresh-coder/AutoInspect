#!/usr/bin/env bash

set -e

echo "Starting AutoInspect FastAPI server..."

echo "Running database migrations..."
alembic upgrade head

exec uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT"