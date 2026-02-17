#!/bin/bash
# Script per creare nuovi database in ClickHouse

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Carica variabili d'ambiente
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | grep -E "CLICKHOUSE" | xargs)
fi

CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-clickhouse_secure_pass_CHANGE_THIS}"
CONTAINER_NAME="${CLICKHOUSE_CONTAINER:-datahub-clickhouse}"

# Funzione per eseguire query ClickHouse
clickhouse_query() {
    docker exec "$CONTAINER_NAME" clickhouse-client \
        --password="$CLICKHOUSE_PASSWORD" \
        --query="$1" 2>&1
}

echo "=========================================="
echo "Creazione Database ClickHouse"
echo "=========================================="
echo ""

# Verifica che il container sia in esecuzione
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME non trovato o non in esecuzione!"
    echo "   Avvia ClickHouse: docker compose up -d clickhouse"
    exit 1
fi

# Se il nome del database è passato come argomento
if [ -n "$1" ]; then
    DB_NAME="$1"
else
    # Chiedi il nome del database
    echo "📊 Database esistenti:"
    clickhouse_query "SHOW DATABASES" | grep -v -E "(INFORMATION_SCHEMA|information_schema|system|default)" || echo "   (nessun database custom)"
    echo ""
    read -p "Inserisci il nome del nuovo database: " DB_NAME
fi

# Valida il nome del database
if [ -z "$DB_NAME" ]; then
    echo "❌ Nome database non valido"
    exit 1
fi

# Verifica che il nome contenga solo caratteri validi
if ! [[ "$DB_NAME" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "❌ Nome database non valido. Usa solo lettere, numeri e underscore"
    exit 1
fi

# Verifica se il database esiste già
if clickhouse_query "SHOW DATABASES" | grep -q "^${DB_NAME}$"; then
    echo "⚠️  Database '$DB_NAME' esiste già!"
    read -p "Vuoi eliminarlo e ricrearlo? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Eliminazione database esistente..."
        clickhouse_query "DROP DATABASE IF EXISTS $DB_NAME" > /dev/null 2>&1 || true
    else
        echo "❌ Operazione annullata"
        exit 0
    fi
fi

# Crea il database
echo "📦 Creazione database '$DB_NAME'..."
if clickhouse_query "CREATE DATABASE IF NOT EXISTS $DB_NAME"; then
    echo "✅ Database '$DB_NAME' creato con successo!"
else
    echo "❌ Errore nella creazione del database"
    exit 1
fi

# Verifica
echo ""
echo "📊 Verifica:"
if clickhouse_query "SHOW DATABASES" | grep -q "^${DB_NAME}$"; then
    echo "   ✅ Database '$DB_NAME' presente nella lista"
else
    echo "   ❌ Database non trovato (errore)"
    exit 1
fi

echo ""
echo "✅ Completato!"
echo ""
echo "💡 Prossimi passi:"
echo "   1. Configura Airbyte Destination per usare database: $DB_NAME"
echo "   2. Aggiungi database in Metabase: Settings → Databases → Add database"
echo "   3. Configura utenti/ruoli/accessi in Metabase per questo database"
