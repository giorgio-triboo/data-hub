#!/bin/bash
# Script per migrazione da MinIO/Presto a ClickHouse
# Smonta i volumi vecchi e prepara i nuovi volumi ClickHouse

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Migrazione a ClickHouse"
echo "=========================================="
echo ""

# Verifica che docker-compose sia disponibile
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker non trovato. Installa Docker prima di continuare."
    exit 1
fi

# Vai nella directory del progetto
cd "$PROJECT_ROOT"

echo "📦 Step 1: Fermare i container esistenti..."
if docker-compose ps | grep -q "minio\|presto"; then
    echo "   Fermando MinIO e Presto..."
    docker-compose stop minio presto 2>/dev/null || true
    docker-compose rm -f minio presto 2>/dev/null || true
    echo "   ✓ Container fermati"
else
    echo "   ✓ Nessun container MinIO/Presto in esecuzione"
fi

echo ""
echo "💾 Step 2: Backup volumi vecchi (opzionale)..."
if [ -d "volumes/minio" ] && [ "$(ls -A volumes/minio 2>/dev/null)" ]; then
    BACKUP_DIR="volumes/backup_minio_$(date +%Y%m%d_%H%M%S)"
    echo "   Creando backup di volumes/minio in $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    cp -r volumes/minio "$BACKUP_DIR/" 2>/dev/null || true
    echo "   ✓ Backup creato in $BACKUP_DIR"
fi

if [ -d "volumes/presto" ] && [ "$(ls -A volumes/presto 2>/dev/null)" ]; then
    BACKUP_DIR="volumes/backup_presto_$(date +%Y%m%d_%H%M%S)"
    echo "   Creando backup di volumes/presto in $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    cp -r volumes/presto "$BACKUP_DIR/" 2>/dev/null || true
    echo "   ✓ Backup creato in $BACKUP_DIR"
fi

echo ""
echo "🗑️  Step 3: Rimozione volumi vecchi..."
if [ -d "volumes/minio" ]; then
    echo "   Rimuovendo volumes/minio..."
    rm -rf volumes/minio
    echo "   ✓ volumes/minio rimosso"
fi

if [ -d "volumes/presto" ]; then
    echo "   Rimuovendo volumes/presto..."
    rm -rf volumes/presto
    echo "   ✓ volumes/presto rimosso"
fi

# Rimuovi anche la directory presto/config se esiste
if [ -d "presto" ]; then
    echo "   Rimuovendo directory presto/config..."
    rm -rf presto
    echo "   ✓ directory presto rimossa"
fi

echo ""
echo "📁 Step 4: Creazione nuovi volumi ClickHouse..."
mkdir -p volumes/clickhouse/data
mkdir -p volumes/clickhouse/log
chmod -R 777 volumes/clickhouse 2>/dev/null || chmod -R 755 volumes/clickhouse
echo "   ✓ Directory volumi ClickHouse create"

echo ""
echo "🔧 Step 5: Verifica configurazione..."
if [ ! -f "clickhouse/config/config.xml" ]; then
    echo "   ⚠️  File clickhouse/config/config.xml non trovato!"
    echo "   Assicurati che la configurazione ClickHouse sia stata creata."
    exit 1
fi
echo "   ✓ Configurazione ClickHouse presente"

echo ""
echo "🐳 Step 6: Preparazione Docker network..."
if ! docker network ls | grep -q "datahub-network"; then
    echo "   Creando network datahub-network..."
    docker network create datahub-network
    echo "   ✓ Network creata"
else
    echo "   ✓ Network già esistente"
fi

echo ""
echo "=========================================="
echo "✅ Migrazione completata!"
echo "=========================================="
echo ""
echo "Prossimi passi:"
echo "1. Verifica le variabili in .env (CLICKHOUSE_*)"
echo "2. Avvia i container: docker-compose up -d"
echo "3. Verifica ClickHouse: curl http://localhost:18123/ping"
echo "4. Configura Airbyte per scrivere su ClickHouse"
echo "5. Configura Metabase per leggere da ClickHouse"
echo ""
echo "⚠️  NOTA: I dati vecchi in MinIO/Presto sono stati salvati in backup"
echo "   se esistevano. Controlla volumes/backup_* per i backup."
echo ""
