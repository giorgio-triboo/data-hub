#!/bin/bash

# DataHub Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Starting DataHub Services"
echo "=========================================="
echo ""

# Verifica che .env esista
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  Error: .env file not found!"
    echo "Run ./scripts/setup.sh first"
    exit 1
fi

# Build wrapper se necessario
echo "Building wrapper application..."
docker-compose build wrapper

# Avvia servizi
echo ""
echo "Starting all services..."
docker-compose up -d

# Attendi che i servizi siano pronti
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Avvia Airbyte se installato
echo ""
echo "Checking Airbyte status..."
if command -v abctl &> /dev/null; then
    if abctl local status 2>&1 | grep -q "does not appear to be installed"; then
        echo "ℹ️  Airbyte non installato. Prima installazione: ./scripts/setup-airbyte.sh (richiede 10-30 min)"
    else
        echo "Starting Airbyte..."
        if abctl local start &>/dev/null; then
            echo "✅ Airbyte started"
        else
            echo "⚠️  Airbyte già in esecuzione o avvio fallito. Verifica: abctl local status"
        fi
    fi
else
    echo "ℹ️  abctl non trovato. Installa: curl -LsfS https://get.airbyte.com | bash -"
fi

# Mostra stato
echo ""
echo "Service status:"
docker-compose ps

# Mostra stato Airbyte se disponibile
if command -v abctl &> /dev/null && ! abctl local status 2>&1 | grep -q "does not appear to be installed"; then
    echo ""
    echo "Airbyte status:"
    abctl local status
fi

echo ""
echo "=========================================="
echo "DataHub started!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Dashboard:     http://localhost:18080"
echo "  - Metabase:      http://localhost:13000"
if command -v abctl &> /dev/null && ! abctl local status 2>&1 | grep -q "does not appear to be installed"; then
    echo "  - Airbyte:       http://localhost:8000"
else
    echo "  - Airbyte:       (not installed - run ./scripts/setup-airbyte.sh)"
fi
echo "  - MinIO Console: http://localhost:19001"
echo "  - MinIO API:     http://localhost:19000"
echo ""
echo "View logs: docker-compose logs -f"
echo ""
