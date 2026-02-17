#!/bin/bash
# Comandi rapidi per ClickHouse

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

# Funzione per eseguire query ClickHouse
clickhouse_query() {
    docker exec "$CONTAINER_NAME" clickhouse-client \
        --password="$CLICKHOUSE_PASSWORD" \
        --query="$1" 2>&1
}

case "${1:-help}" in
    list|tables)
        echo "📊 Tabelle in $CLICKHOUSE_DB:"
        clickhouse_query "SHOW TABLES FROM $CLICKHOUSE_DB"
        ;;
    
    count)
        TABLE="${2:-}"
        if [ -z "$TABLE" ]; then
            echo "❌ Specifica il nome della tabella"
            echo "   Uso: $0 count <table_name>"
            exit 1
        fi
        echo "📊 Record in $CLICKHOUSE_DB.$TABLE:"
        clickhouse_query "SELECT COUNT(*) FROM $CLICKHOUSE_DB.$TABLE"
        ;;
    
    truncate)
        TABLE="${2:-}"
        if [ -z "$TABLE" ]; then
            echo "❌ Specifica il nome della tabella"
            echo "   Uso: $0 truncate <table_name>"
            exit 1
        fi
        echo "🧹 Svuotamento tabella $CLICKHOUSE_DB.$TABLE..."
        clickhouse_query "TRUNCATE TABLE IF EXISTS $CLICKHOUSE_DB.$TABLE"
        echo "✅ Tabella svuotata!"
        ;;
    
    drop)
        TABLE="${2:-}"
        if [ -z "$TABLE" ]; then
            echo "❌ Specifica il nome della tabella"
            echo "   Uso: $0 drop <table_name>"
            exit 1
        fi
        echo "🗑️  Eliminazione tabella $CLICKHOUSE_DB.$TABLE..."
        clickhouse_query "DROP TABLE IF EXISTS $CLICKHOUSE_DB.$TABLE"
        echo "✅ Tabella eliminata!"
        ;;
    
    clean-all)
        echo "🧹 Pulizia completa database $CLICKHOUSE_DB..."
        TABLES=$(clickhouse_query "SHOW TABLES FROM $CLICKHOUSE_DB" | grep -v "^$" || echo "")
        if [ -z "$TABLES" ]; then
            echo "   Database già pulito!"
            exit 0
        fi
        echo "$TABLES" | while read -r table; do
            if [ -n "$table" ]; then
                echo "   Dropping: $table"
                clickhouse_query "DROP TABLE IF EXISTS $CLICKHOUSE_DB.$table" > /dev/null 2>&1 || true
            fi
        done
        echo "✅ Tutte le tabelle eliminate!"
        ;;
    
    query)
        QUERY="${2:-}"
        if [ -z "$QUERY" ]; then
            echo "❌ Specifica la query SQL"
            echo "   Uso: $0 query \"SELECT * FROM table LIMIT 10\""
            exit 1
        fi
        clickhouse_query "$QUERY"
        ;;
    
    client)
        echo "🔌 Apertura ClickHouse client interattivo..."
        docker exec -it "$CONTAINER_NAME" clickhouse-client --password="$CLICKHOUSE_PASSWORD"
        ;;
    
    help|*)
        echo "Comandi rapidi ClickHouse"
        echo ""
        echo "Uso: $0 <comando> [argomenti]"
        echo ""
        echo "Comandi disponibili:"
        echo "  list, tables              - Lista tutte le tabelle"
        echo "  count <table>             - Conta record in una tabella"
        echo "  truncate <table>         - Svuota una tabella (mantiene struttura)"
        echo "  drop <table>             - Elimina una tabella"
        echo "  clean-all                - Elimina tutte le tabelle"
        echo "  query \"<sql>\"           - Esegue una query SQL"
        echo "  client                   - Apre client interattivo"
        echo ""
        echo "Esempi:"
        echo "  $0 list"
        echo "  $0 count campaigns"
        echo "  $0 truncate ads_insights"
        echo "  $0 query \"SELECT * FROM campaigns LIMIT 5\""
        echo "  $0 clean-all"
        ;;
esac
