#!/bin/bash

# DataHub Healthcheck Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "DataHub Healthcheck"
echo "=========================================="
echo ""

# Verifica container
echo "Container status:"
docker-compose ps

echo ""
echo "=========================================="
echo "Service Health Checks"
echo "=========================================="
echo ""

# PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec -T postgres-metabase pg_isready -U metabase > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# MySQL
echo -n "MySQL: "
if docker-compose exec -T mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD:-mysql_root_pass} > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# MinIO
echo -n "MinIO: "
if curl -sf http://localhost:19000/minio/health/live > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Airbyte Webapp
echo -n "Airbyte Webapp: "
if curl -sf http://localhost:18000/api/v1/health > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Airbyte Server
echo -n "Airbyte Server: "
if curl -sf http://localhost:18001/api/v1/health > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Metabase
echo -n "Metabase: "
if curl -sf http://localhost:13000/api/health > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

echo ""
echo "=========================================="
echo "Wrapper Logs (last 20 lines)"
echo "=========================================="
echo ""

docker-compose logs --tail=20 wrapper

echo ""
