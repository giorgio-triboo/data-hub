#!/bin/bash
# Script per installare e configurare Airbyte tramite abctl

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Airbyte Setup con abctl"
echo "=========================================="
echo ""

# Verifica che abctl sia installato
if ! command -v abctl &> /dev/null; then
    echo "❌ abctl non trovato!"
    echo "   Installa abctl: curl -LsfS https://get.airbyte.com | bash -"
    exit 1
fi

echo "✅ abctl trovato: $(abctl version)"
echo ""

# Verifica stato installazione esistente (abctl status può uscire 0 anche se "not installed")
if abctl local status 2>&1 | grep -q "does not appear to be installed"; then
    : # Non installato, procedi con l'installazione sotto
else
    echo "⚠️  Airbyte è già installato"
    echo ""
    echo "Comandi utili:"
    echo "  abctl local status       - Verifica stato"
    echo "  abctl local credentials  - Ottieni credenziali"
    echo "  abctl local uninstall    - Disinstalla"
    echo ""
    read -p "Vuoi reinstallare? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installazione annullata. Per avviare Airbyte: abctl local start"
        exit 0
    fi
    echo "Disinstallazione versione esistente..."
    abctl local uninstall
fi

echo ""
echo "📦 Installazione Airbyte..."
echo "   Questo richiederà 10-30 minuti..."
echo ""

# Installa Airbyte
if abctl local install --port=8000 --no-browser; then
    echo ""
    echo "✅ Airbyte installato con successo!"
    echo ""
    echo "📋 Credenziali:"
    abctl local credentials
    echo ""
    echo "🌐 Accesso:"
    echo "   URL: http://localhost:8000"
    echo ""
    echo "📝 Prossimi passi:"
    echo "   1. Accedi a http://localhost:8000"
    echo "   2. Configura MinIO come destinazione S3:"
    echo "      - Endpoint: http://minio:9000 (o localhost:19000 dall'host)"
    echo "      - Access Key: minioadmin"
    echo "      - Secret Key: (vedi .env)"
    echo "      - Bucket: marketing-data"
    echo "      - Format: Parquet"
    echo ""
    echo "🔧 Comandi utili:"
    echo "   abctl local status       - Verifica stato"
    echo "   abctl local credentials  - Mostra credenziali"
    echo "   abctl local uninstall    - Disinstalla"
else
    echo ""
    echo "❌ Installazione fallita"
    echo "   Verifica i log per dettagli"
    exit 1
fi
