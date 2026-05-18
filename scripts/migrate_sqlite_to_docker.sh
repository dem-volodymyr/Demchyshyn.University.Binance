#!/usr/bin/env bash
# Migrate data from local SQLite into PostgreSQL in Docker.
# Usage: ./scripts/migrate_sqlite_to_docker.sh [path/to/db.sqlite3]

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SQLITE_PATH="${1:-db.sqlite3}"
FIXTURE="fixtures/sqlite_export.json"
RESET="${RESET_POSTGRES:-0}"

if [[ ! -f "$SQLITE_PATH" ]]; then
  echo "SQLite file not found: $SQLITE_PATH" >&2
  exit 1
fi

echo "==> 1/4 Export from SQLite"
unset DATABASE_URL DJANGO_DB_NAME
python manage.py export_sqlite_fixture --sqlite "$SQLITE_PATH" --output "$FIXTURE"

if [[ "$RESET" == "1" ]]; then
  echo "==> Resetting Postgres volume"
  docker compose down -v
fi

echo "==> 2/4 Migrate Postgres"
docker compose up -d db
docker compose run --rm web python manage.py migrate --noinput

echo "==> 3/4 Load fixture"
docker compose run --rm web python manage.py loaddata "$FIXTURE"

echo "==> 4/4 Start web"
docker compose up -d web

echo "Done. Open http://localhost:8000"
