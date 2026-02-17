#!/bin/bash
# Script per pulire il database ClickHouse per test puliti

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Carica variabili d'ambiente
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | grep -E "CLICKHOUSE" | xargs)
fi

CLICKHOUSE_DB="${CLICKHOUSE_DB:-marketing_data}"
CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-clickhouse_secure_pass_CHANGE_THIS}"
CONTAINER_NAME="${CLICKHOUSE_CONTAINER:-datahub-clickhouse}"

echo "=========================================="
echo "Pulizia Database ClickHouse"
echo "=========================================="
echo ""
echo "Database: $CLICKHOUSE_DB"
echo "Container: $CONTAINER_NAME"
echo ""

# Verifica che il container sia in esecuzione
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME non trovato o non in esecuzione!"
    echo "   Avvia ClickHouse: docker compose up -d clickhouse"
    exit 1
fi

# Funzione per eseguire query ClickHouse
clickhouse_query() {
    docker exec "$CONTAINER_NAME" clickhouse-client \
        --password="$CLICKHOUSE_PASSWORD" \
        --query="$1" 2>&1
}

# Lista tabelle esistenti
echo "📊 Tabelle esistenti nel database $CLICKHOUSE_DB:"
echo ""
TABLES=$(clickhouse_query "SHOW TABLES FROM $CLICKHOUSE_DB" | grep -v "^$" || echo "")

if [ -z "$TABLES" ]; then
    echo "   (nessuna tabella trovata)"
    echo ""
    echo "✅ Database già pulito!"
    exit 0
fi

echo "$TABLES" | while read -r table; do
    if [ -n "$table" ]; then
        COUNT=$(clickhouse_query "SELECT COUNT(*) FROM $CLICKHOUSE_DB.$table" 2>/dev/null || echo "0")
        echo "   - $table ($COUNT record)"
    fi
done
echo ""

# Chiedi conferma
read -p "⚠️  Vuoi procedere con la pulizia? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operazione annullata"
    exit 0
fi

# Opzioni di pulizia
echo ""
echo "Scegli il tipo di pulizia:"
echo "  1) TRUNCATE - Svuota le tabelle (mantiene la struttura)"
echo "  2) DROP - Elimina completamente le tabelle"
echo "  3) DROP e ricrea database (pulizia completa)"
read -p "Scelta (1/2/3) [default: 1]: " -n 1 -r
echo ""

CLEAN_TYPE="${REPLY:-1}"

case $CLEAN_TYPE in
    1)
        echo "🧹 Svuotamento tabelle (TRUNCATE)..."
        echo "$TABLES" | while read -r table; do
            if [ -n "$table" ]; then
                echo "   Truncating: $table"
                clickhouse_query "TRUNCATE TABLE IF EXISTS $CLICKHOUSE_DB.$table" > /dev/null 2>&1 || true
            fi
        done
        echo "✅ Tabelle svuotate!"
        ;;
    2)
        echo "🗑️  Eliminazione tabelle (DROP)..."
        echo "$TABLES" | while read -r table; do
            if [ -n "$table" ]; then
                echo "   Dropping: $table"
                clickhouse_query "DROP TABLE IF EXISTS $CLICKHOUSE_DB.$table" > /dev/null 2>&1 || true
            fi
        done
        echo "✅ Tabelle eliminate!"
        ;;
    3)
        echo "🔥 Pulizia completa (DROP DATABASE)..."
        read -p "⚠️  ATTENZIONE: Questo eliminerà TUTTO il database! Continuare? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Operazione annullata"
            exit 0
        fi
        
        # Elimina tutte le tabelle prima
        echo "$TABLES" | while read -r table; do
            if [ -n "$table" ]; then
                clickhouse_query "DROP TABLE IF EXISTS $CLICKHOUSE_DB.$table" > /dev/null 2>&1 || true
            fi
        done
        
        # Ricrea il database
        echo "   Ricreazione database..."
        clickhouse_query "DROP DATABASE IF EXISTS $CLICKHOUSE_DB" > /dev/null 2>&1 || true
        clickhouse_query "CREATE DATABASE IF NOT EXISTS $CLICKHOUSE_DB" > /dev/null 2>&1 || true
        echo "✅ Database ricreato!"
        ;;
    *)
        echo "❌ Scelta non valida"
        exit 1
        ;;
esac

# Verifica finale
echo ""
echo "📊 Verifica finale:"
FINAL_TABLES=$(clickhouse_query "SHOW TABLES FROM $CLICKHOUSE_DB" 2>/dev/null | grep -v "^$" || echo "")

if [ -z "$FINAL_TABLES" ]; then
    echo "   ✅ Database pulito: nessuna tabella trovata"
else
    echo "   Tabelle rimanenti:"
    echo "$FINAL_TABLES" | while read -r table; do
        if [ -n "$table" ]; then
            COUNT=$(clickhouse_query "SELECT COUNT(*) FROM $CLICKHOUSE_DB.$table" 2>/dev/null || echo "0")
            echo "     - $table ($COUNT record)"
        fi
    done
fi

echo ""
echo "✅ Pulizia completata!"
echo ""
echo "💡 Prossimi passi:"
echo "   1. Riavvia le sync in Airbyte per ricaricare i dati"
echo "   2. Verifica i dati in Metabase dopo la sync"
