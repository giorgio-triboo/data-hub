#!/bin/bash
# Script di verifica rapida per ClickHouse

set -e

echo "=========================================="
echo "Verifica Configurazione ClickHouse"
echo "=========================================="
echo ""

# Verifica ClickHouse container
echo "📦 Verifica Container ClickHouse..."
if docker-compose ps clickhouse | grep -q "Up"; then
    echo "   ✓ ClickHouse container è attivo"
else
    echo "   ✗ ClickHouse container non è attivo"
    echo "   Avvia con: docker-compose up -d clickhouse"
    exit 1
fi

# Verifica healthcheck
echo ""
echo "🏥 Verifica Healthcheck..."
if curl -s http://localhost:18123/ping | grep -q "Ok"; then
    echo "   ✓ ClickHouse risponde correttamente (HTTP)"
else
    echo "   ✗ ClickHouse non risponde su porta 8123"
    exit 1
fi

# Verifica variabili ambiente
echo ""
echo "🔧 Verifica Variabili Ambiente..."
if [ -f ".env" ]; then
    if grep -q "CLICKHOUSE_DB" .env; then
        CLICKHOUSE_DB=$(grep "CLICKHOUSE_DB" .env | cut -d'=' -f2 | tr -d ' ')
        echo "   ✓ CLICKHOUSE_DB: $CLICKHOUSE_DB"
    else
        echo "   ⚠️  CLICKHOUSE_DB non trovato in .env"
    fi
    
    if grep -q "CLICKHOUSE_USER" .env; then
        CLICKHOUSE_USER=$(grep "CLICKHOUSE_USER" .env | cut -d'=' -f2 | tr -d ' ')
        echo "   ✓ CLICKHOUSE_USER: $CLICKHOUSE_USER"
    else
        echo "   ⚠️  CLICKHOUSE_USER non trovato in .env"
    fi
    
    if grep -q "CLICKHOUSE_PASSWORD" .env; then
        echo "   ✓ CLICKHOUSE_PASSWORD: [configurato]"
    else
        echo "   ⚠️  CLICKHOUSE_PASSWORD non trovato in .env"
    fi
else
    echo "   ⚠️  File .env non trovato"
fi

# Verifica database
echo ""
echo "🗄️  Verifica Database..."
if docker-compose exec -T clickhouse clickhouse-client --query "SHOW DATABASES" 2>/dev/null | grep -q "marketing_data"; then
    echo "   ✓ Database 'marketing_data' esiste"
else
    echo "   ⚠️  Database 'marketing_data' non trovato"
    echo "   Creazione database..."
    docker-compose exec -T clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS marketing_data" 2>/dev/null
    echo "   ✓ Database creato"
fi

# Verifica porte
echo ""
echo "🔌 Verifica Porte..."
PORTS=(18123 19000 19004)
PORT_NAMES=("HTTP (8123)" "Native (9000)" "Inter-server (9004)")
for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    if nc -z localhost $PORT 2>/dev/null; then
        echo "   ✓ Porta $PORT ($NAME) è aperta"
    else
        echo "   ✗ Porta $PORT ($NAME) non è raggiungibile"
    fi
done

# Verifica volumi
echo ""
echo "💾 Verifica Volumi..."
if [ -d "volumes/clickhouse/data" ]; then
    SIZE=$(du -sh volumes/clickhouse/data 2>/dev/null | cut -f1)
    echo "   ✓ Volume dati: $SIZE"
else
    echo "   ⚠️  Directory volumes/clickhouse/data non trovata"
fi

if [ -d "volumes/clickhouse/log" ]; then
    echo "   ✓ Volume log presente"
else
    echo "   ⚠️  Directory volumes/clickhouse/log non trovata"
fi

# Verifica configurazione
echo ""
echo "⚙️  Verifica Configurazione..."
if [ -f "clickhouse/config/config.xml" ]; then
    echo "   ✓ File config.xml presente"
else
    echo "   ✗ File config.xml non trovato"
fi

if [ -f "clickhouse/users/users.xml" ]; then
    echo "   ✓ File users.xml presente"
else
    echo "   ✗ File users.xml non trovato"
fi

# Test connessione
echo ""
echo "🔗 Test Connessione..."
if docker-compose exec -T clickhouse clickhouse-client --query "SELECT 1" 2>/dev/null > /dev/null; then
    echo "   ✓ Connessione ClickHouse funzionante"
else
    echo "   ✗ Errore nella connessione ClickHouse"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Verifica Completata!"
echo "=========================================="
echo ""
echo "ClickHouse è pronto per essere configurato in:"
echo "  - Airbyte: http://localhost:8000"
echo "  - Metabase: http://localhost:13000"
echo ""
echo "Guida completa: doc/CLICKHOUSE_SETUP.md"
echo ""
