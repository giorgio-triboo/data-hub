#!/bin/bash

# DataHub Update Script
# Aggiorna i servizi alle ultime versioni disponibili

set -e

# Se eseguito dal wrapper Docker, usa /app come root
if [ -d "/app" ] && [ -f "/app/docker-compose.yml" ]; then
    PROJECT_ROOT="/app"
    cd "$PROJECT_ROOT"
    # Usa docker-compose dal path assoluto
    DOCKER_COMPOSE_CMD="docker-compose -f /app/docker-compose.yml"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    cd "$PROJECT_ROOT"
    DOCKER_COMPOSE_CMD="docker-compose"
fi

echo "=========================================="
echo "DataHub Update Script"
echo "=========================================="
echo ""

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funzione per backup
backup_volumes() {
    echo -e "${YELLOW}Creating backup...${NC}"
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup volumi
    if [ -d "volumes" ]; then
        echo "Backing up volumes..."
        tar -czf "$BACKUP_DIR/volumes.tar.gz" volumes/ 2>/dev/null || true
    fi
    
    # Backup docker-compose.yml
    cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"
    
    echo -e "${GREEN}Backup created in $BACKUP_DIR${NC}"
    echo ""
}

# Funzione per aggiornare versione in docker-compose.yml
update_version() {
    local service=$1
    local current_version=$2
    local new_version=$3
    
    echo -e "${YELLOW}Updating $service: $current_version → $new_version${NC}"
    
    case $service in
        "MySQL")
            # Aggiorna immagine MySQL
            sed -i.bak "s|image: mysql:.*|image: mysql:$new_version|g" docker-compose.yml
            ;;
        "PostgreSQL")
            # Aggiorna immagine PostgreSQL
            sed -i.bak "s|image: postgres:.*|image: postgres:$new_version|g" docker-compose.yml
            ;;
        "Metabase")
            # Metabase usa sempre 'latest', ma possiamo specificare una versione
            if [ "$new_version" != "latest" ]; then
                sed -i.bak "s|image: metabase/metabase:.*|image: metabase/metabase:v$new_version|g" docker-compose.yml
            fi
            ;;
        "MinIO")
            # MinIO usa sempre 'latest', ma possiamo specificare una versione
            if [ "$new_version" != "latest" ]; then
                sed -i.bak "s|image: minio/minio:.*|image: minio/minio:$new_version|g" docker-compose.yml
            fi
            ;;
    esac
    
    # Rimuovi file backup di sed
    rm -f docker-compose.yml.bak
}

# Funzione per aggiornare un servizio specifico
update_service() {
    local service_name=$1
    
    echo ""
    echo "=========================================="
    echo "Updating $service_name"
    echo "=========================================="
    
    # Stop del servizio
    echo -e "${YELLOW}Stopping $service_name...${NC}"
    $DOCKER_COMPOSE_CMD stop "$service_name" || true
    
    # Pull nuova immagine
    echo -e "${YELLOW}Pulling new image for $service_name...${NC}"
    $DOCKER_COMPOSE_CMD pull "$service_name"
    
    # Ricrea container
    echo -e "${YELLOW}Recreating container for $service_name...${NC}"
    $DOCKER_COMPOSE_CMD up -d --force-recreate "$service_name"
    
    # Attendi che il servizio sia healthy
    echo -e "${YELLOW}Waiting for $service_name to be healthy...${NC}"
    sleep 10
    
    # Verifica stato
    if $DOCKER_COMPOSE_CMD ps "$service_name" | grep -q "healthy\|Up"; then
        echo -e "${GREEN}✓ $service_name updated successfully${NC}"
    else
        echo -e "${RED}✗ $service_name update failed${NC}"
        return 1
    fi
}

# Funzione per aggiornare tutti i servizi con aggiornamenti disponibili
update_all() {
    echo "Checking for available updates..."
    
    # Ottieni informazioni versioni dall'API
    # Se siamo nel container wrapper, usa localhost, altrimenti usa il nome del servizio
    if [ -d "/app" ]; then
        API_URL="http://localhost:8080/api/versions"
    else
        API_URL="http://localhost:18080/api/versions"
    fi
    VERSION_INFO=$(curl -s "$API_URL" 2>/dev/null || echo '{}')
    
    if [ "$VERSION_INFO" = "{}" ]; then
        echo -e "${RED}Error: Cannot connect to version API. Is the wrapper running?${NC}"
        exit 1
    fi
    
    # Estrai servizi con aggiornamenti disponibili
    UPDATES=$(echo "$VERSION_INFO" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for key, service in data.get('services', {}).items():
    if service.get('update_available'):
        print(f\"{service['service']}|{service['current']}|{service['latest']}\")
" 2>/dev/null)
    
    if [ -z "$UPDATES" ]; then
        echo -e "${GREEN}No updates available!${NC}"
        exit 0
    fi
    
    echo ""
    echo "Found updates:"
    echo "$UPDATES" | while IFS='|' read -r service current latest; do
        echo "  - $service: $current → $latest"
    done
    echo ""
    
    # Chiedi conferma
    read -p "Do you want to proceed with updates? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled."
        exit 0
    fi
    
    # Backup
    backup_volumes
    
    # Aggiorna ogni servizio
    while IFS='|' read -r service current latest; do
        # Mappa nome servizio a nome docker-compose
        case $service in
            "MySQL")
                compose_service="mysql"
                update_version "MySQL" "$current" "$latest"
                update_service "$compose_service"
                ;;
            "PostgreSQL")
                compose_service="postgres-metabase"
                update_version "PostgreSQL" "$current" "$latest"
                update_service "$compose_service"
                ;;
            "Metabase")
                compose_service="metabase"
                update_version "Metabase" "$current" "$latest"
                update_service "$compose_service"
                ;;
            "MinIO")
                compose_service="minio"
                update_version "MinIO" "$current" "$latest"
                update_service "$compose_service"
                ;;
            *)
                echo -e "${YELLOW}Skipping $service (not supported for auto-update)${NC}"
                ;;
        esac
    done <<< "$UPDATES"
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Update completed!${NC}"
    echo "=========================================="
    echo ""
    echo "Verifying services..."
    $DOCKER_COMPOSE_CMD ps
    echo ""
    echo "Run healthcheck: ./scripts/healthcheck.sh"
}

# Funzione per aggiornare un singolo servizio
update_single() {
    local service=$1
    local version=$2
    
    if [ -z "$service" ] || [ -z "$version" ]; then
        echo "Usage: $0 single <service> <version>"
        echo "Example: $0 single mysql 8.1"
        exit 1
    fi
    
    backup_volumes
    
        # Mappa nome servizio a nome docker-compose
        case $service in
            mysql)
                compose_service="mysql"
                update_version "MySQL" "current" "$version"
                ;;
            postgres|postgres-metabase)
                compose_service="postgres-metabase"
                update_version "PostgreSQL" "current" "$version"
                ;;
            metabase)
                compose_service="metabase"
                update_version "Metabase" "current" "$version"
                ;;
            minio)
                compose_service="minio"
                update_version "MinIO" "current" "$version"
                ;;
            *)
                echo -e "${RED}Unknown service: $service${NC}"
                exit 1
                ;;
        esac
        
        update_service "$compose_service"
}

# Main
case "${1:-all}" in
    all)
        update_all
        ;;
    single)
        update_single "$2" "$3"
        ;;
    backup)
        backup_volumes
        ;;
    *)
        echo "Usage: $0 [all|single|backup]"
        echo ""
        echo "Commands:"
        echo "  all          - Update all services with available updates"
        echo "  single       - Update a single service: $0 single <service> <version>"
        echo "  backup       - Create backup only"
        echo ""
        echo "Examples:"
        echo "  $0 all"
        echo "  $0 single mysql 8.1"
        echo "  $0 single postgres 16-alpine"
        exit 1
        ;;
esac
