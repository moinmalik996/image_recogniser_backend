#!/usr/bin/env sh
set -eu

# Run migrations on container startup (retry briefly for DB readiness).
tries=30
count=0
while true; do
  if alembic upgrade head; then
    break
  fi
  count=$((count + 1))
  if [ "$count" -ge "$tries" ]; then
    echo "Alembic migrations failed after ${tries} attempts." >&2
    exit 1
  fi
  echo "Waiting for database... (${count}/${tries})" >&2
  sleep 1
done

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
