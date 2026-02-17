#!/bin/bash
# Reset completo: ferma container, rimuove volumi e immagini del progetto
# per simulare una nuova installazione.
# Uso: ./scripts/fresh-install-reset.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "DataHub - Reset per nuova installazione"
echo "=========================================="
echo ""

echo "1. Fermando e rimuovendo container, volumi named e immagini del progetto..."
docker compose down -v --rmi all || true
# Nota: immagini base (es. postgres, mysql) possono restare se usate da altri container

echo ""
echo "2. Rimuovendo dati nei volumi bind-mount (./volumes/)..."
rm -rf ./volumes/postgres
rm -rf ./volumes/mysql
rm -rf ./volumes/clickhouse
rm -rf ./volumes/metabase
rm -rf ./volumes/logs
rm -rf ./volumes/backups

echo ""
echo "3. Ricreando directory volumes (vuote)..."
mkdir -p ./volumes/postgres ./volumes/mysql ./volumes/clickhouse/data ./volumes/clickhouse/log
mkdir -p ./volumes/metabase ./volumes/logs ./volumes/backups

echo ""
echo "=========================================="
echo "Reset completato."
echo "Per una nuova installazione:"
echo "  docker compose build"
echo "  docker compose up -d"
echo "=========================================="
