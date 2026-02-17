#!/bin/bash

# DataHub Stop Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Stopping DataHub Services"
echo "=========================================="
echo ""

docker-compose stop

echo ""
echo "Services stopped."
echo ""
echo "To remove containers: docker-compose down"
echo "To remove containers and volumes: docker-compose down -v"
echo ""
