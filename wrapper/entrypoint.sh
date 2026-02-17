#!/bin/sh
# Attende che PostgreSQL sia raggiungibile prima di avviare supervisord,
# così il processo wrapper non esce con status 1 al primo avvio.

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
MAX_TRIES=60
SLEEP=2

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
i=0
while [ $i -lt $MAX_TRIES ]; do
  if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -q 2>/dev/null; then
    echo "PostgreSQL is ready."
    break
  fi
  i=$((i + 1))
  if [ $i -eq $MAX_TRIES ]; then
    echo "WARNING: PostgreSQL not ready after ${MAX_TRIES} attempts. Starting anyway."
  fi
  sleep $SLEEP
done

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisor.conf -n
