#!/bin/bash

# DataHub Setup Script
# Crea le directory necessarie e configura l'ambiente

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "DataHub Setup Script"
echo "=========================================="
echo ""

# Crea directory per volumi
echo "Creating volume directories..."
mkdir -p "$PROJECT_ROOT/volumes/postgres"
mkdir -p "$PROJECT_ROOT/volumes/mysql"
mkdir -p "$PROJECT_ROOT/volumes/minio"
mkdir -p "$PROJECT_ROOT/volumes/airbyte-workspace"
mkdir -p "$PROJECT_ROOT/volumes/metabase"
mkdir -p "$PROJECT_ROOT/volumes/temporal"
mkdir -p "$PROJECT_ROOT/volumes/logs"
mkdir -p "$PROJECT_ROOT/volumes/backups"

# Imposta permessi
echo "Setting permissions..."
chmod -R 755 "$PROJECT_ROOT/volumes/"

# Crea .env se non esiste
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Creating .env file from .env.example..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "⚠️  IMPORTANT: Please edit .env file and change all default passwords!"
    else
        echo "⚠️  Warning: .env.example not found. Creating basic .env..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env" 2>/dev/null || cat > "$PROJECT_ROOT/.env" << EOF
# PostgreSQL - Database Condiviso
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_pass_CHANGE_THIS

# Airbyte Database
AIRBYTE_DB_USER=airbyte_user
AIRBYTE_DB_PASSWORD=airbyte_secure_pass_CHANGE_THIS

# Metabase Database
METABASE_DB_USER=metabase_user
METABASE_DB_PASSWORD=metabase_secure_pass_CHANGE_THIS

# Wrapper Database
WRAPPER_DB_USER=wrapper_user
WRAPPER_DB_PASSWORD=wrapper_secure_pass_CHANGE_THIS

# MySQL (CRUD Database)
MYSQL_ROOT_PASSWORD=mysql_root_secure_pass_CHANGE_THIS
MYSQL_DATABASE=datahub_crud
MYSQL_USER=datahub_user
MYSQL_PASSWORD=mysql_secure_pass_CHANGE_THIS

# MinIO (S3 Storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin_secure_pass_CHANGE_THIS

# Airbyte
AIRBYTE_VERSION=0.50.0
AIRBYTE_SERVER_IMAGE=airbyte/server:local
AIRBYTE_WEBAPP_IMAGE=airbyte/webapp:local
AIRBYTE_WORKER_IMAGE=airbyte/worker:local

# Wrapper
CHECK_INTERVAL=60
LOG_LEVEL=INFO
EOF
        echo "⚠️  IMPORTANT: Please edit .env file and change all default passwords!"
    fi
else
    echo "✓ .env file already exists"
fi

echo ""
echo "=========================================="
echo "Setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and change all default passwords"
echo "2. Run: docker-compose build wrapper"
echo "3. Run: docker-compose up -d"
echo ""
