#!/bin/bash
set -e

function create_user_and_database() {
	local database=$1
	local user=$2
	local password=$3
	echo "Creating user and database '$database' with user '$user'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE USER $user WITH PASSWORD '$password';
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $user;
EOSQL
}

# Crea database e utenti per Airbyte
if [ -n "$AIRBYTE_DB_USER" ] && [ -n "$AIRBYTE_DB_PASSWORD" ]; then
	create_user_and_database "airbyte" "$AIRBYTE_DB_USER" "$AIRBYTE_DB_PASSWORD"
fi

# Crea database e utenti per Metabase
if [ -n "$METABASE_DB_USER" ] && [ -n "$METABASE_DB_PASSWORD" ]; then
	create_user_and_database "metabase" "$METABASE_DB_USER" "$METABASE_DB_PASSWORD"
fi

# Crea database e utenti per Wrapper
if [ -n "$WRAPPER_DB_USER" ] && [ -n "$WRAPPER_DB_PASSWORD" ]; then
	create_user_and_database "wrapper_config" "$WRAPPER_DB_USER" "$WRAPPER_DB_PASSWORD"
fi

# Crea database per Temporal (se necessario)
if [ -n "$TEMPORAL_DB_USER" ] && [ -n "$TEMPORAL_DB_PASSWORD" ]; then
	create_user_and_database "temporal" "$TEMPORAL_DB_USER" "$TEMPORAL_DB_PASSWORD"
fi

echo "Multiple databases created"
