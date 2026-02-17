#!/bin/bash
# Script per buildare le immagini Docker di Airbyte localmente

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AIRBYTE_DIR="$PROJECT_ROOT/airbyte-official"

echo "=========================================="
echo "Airbyte Build Script"
echo "=========================================="
echo ""

# Verifica che airbyte-official esista
if [ ! -d "$AIRBYTE_DIR" ]; then
    echo "❌ Directory airbyte-official non trovata!"
    echo "   Clona il repository: git clone https://github.com/airbytehq/airbyte.git airbyte-official"
    exit 1
fi

cd "$AIRBYTE_DIR"

echo "📦 Build codice Java/Kotlin..."
./gradlew build -x test || {
    echo "⚠️  Build fallito, continuo comunque..."
}

echo ""
echo "🐳 Build immagini Docker..."

# Build server
echo "Building airbyte-server..."
docker build -t airbyte/server:local -f airbyte-server/Dockerfile . || {
    echo "❌ Errore build airbyte-server"
    exit 1
}

# Build webapp
echo "Building airbyte-webapp..."
docker build -t airbyte/webapp:local -f airbyte-webapp/Dockerfile . || {
    echo "❌ Errore build airbyte-webapp"
    exit 1
}

# Build worker
echo "Building airbyte-worker..."
docker build -t airbyte/worker:local -f airbyte-workers/Dockerfile . || {
    echo "❌ Errore build airbyte-worker"
    exit 1
}

echo ""
echo "✅ Build completato!"
echo ""
echo "Immagini create:"
docker images | grep "airbyte/.*:local"
echo ""
echo "Ora puoi usare queste immagini nel docker-compose.yml"
echo "Assicurati che .env contenga:"
echo "  AIRBYTE_SERVER_IMAGE=airbyte/server:local"
echo "  AIRBYTE_WEBAPP_IMAGE=airbyte/webapp:local"
echo "  AIRBYTE_WORKER_IMAGE=airbyte/worker:local"
