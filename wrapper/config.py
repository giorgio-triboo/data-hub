#!/usr/bin/env python3
"""
Configuration - Configurazione applicazione
"""

import os
from dotenv import load_dotenv

# Carica .env solo se esiste, ma NON sovrascrive variabili d'ambiente già presenti
# Questo permette alle variabili del docker-compose di avere priorità
load_dotenv(override=False)


class Config:
    """Configurazione base"""
    
    # Flask
    SECRET_KEY = os.getenv('WRAPPER_SECRET_KEY', os.urandom(32).hex())
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Configurazione URL base per OAuth (importante per redirect URI)
    SERVER_NAME = os.getenv('SERVER_NAME', 'localhost:18080')  # Usato da Flask-Dance per costruire redirect URI
    
    # Database PostgreSQL (per utenti, ruoli, audit)
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    # Usa WRAPPER_DB_USER se disponibile, altrimenti POSTGRES_USER
    POSTGRES_USER = os.getenv('WRAPPER_DB_USER') or os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('WRAPPER_DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD', 'postgres_secure_pass_CHANGE_THIS')
    # Usa POSTGRES_DB se disponibile (dal docker-compose), altrimenti WRAPPER_DB_NAME o default
    # Nota: nel docker-compose.yml c'è POSTGRES_DB: wrapper_config
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'wrapper_config')
    
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
    GOOGLE_OAUTH_REDIRECT_URI = os.getenv('GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:8080/auth/google/callback')
    
    # Allowed Google domains (opzionale, lascia vuoto per permettere qualsiasi dominio)
    ALLOWED_GOOGLE_DOMAINS = os.getenv('ALLOWED_GOOGLE_DOMAINS', '').split(',') if os.getenv('ALLOWED_GOOGLE_DOMAINS') else []
    
    # ClickHouse
    CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
    CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', 8123))
    CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
    CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_secure_pass_CHANGE_THIS')
    CLICKHOUSE_DB = os.getenv('CLICKHOUSE_DB', 'marketing_data')
    
    # Airbyte
    AIRBYTE_WEBAPP_URL = os.getenv('AIRBYTE_WEBAPP_URL', 'http://localhost:8000')
    AIRBYTE_API_URL = os.getenv('AIRBYTE_API_URL', 'http://localhost:8000/api/v1')
    
    # Healthcheck
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Wrapper
    WRAPPER_PORT = int(os.getenv('WRAPPER_PORT', '8080'))
