#!/usr/bin/env python3
"""
ClickHouse Service - Servizio per gestione database ClickHouse
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)


class ClickHouseService:
    """Servizio per gestione database ClickHouse"""
    
    def __init__(self):
        self.host = Config.CLICKHOUSE_HOST
        self.port = Config.CLICKHOUSE_PORT
        self.user = Config.CLICKHOUSE_USER
        self.password = Config.CLICKHOUSE_PASSWORD
        self.base_url = f"http://{self.host}:{self.port}"
    
    def _execute_query(self, query: str, database: str = 'default') -> Optional[Any]:
        """Esegue una query ClickHouse via HTTP"""
        try:
            url = f"{self.base_url}/?database={database}"
            params = {
                'query': query,
                'user': self.user,
                'password': self.password
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error executing ClickHouse query: {e}")
            raise
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """Lista tutti i database (esclusi system)"""
        try:
            query = "SHOW DATABASES"
            result = self._execute_query(query)
            
            databases = []
            for db_name in result.split('\n'):
                db_name = db_name.strip()
                if db_name and db_name not in ['system', 'INFORMATION_SCHEMA', 'information_schema', 'default']:
                    db_info = self.get_database_info(db_name)
                    databases.append(db_info)
            
            return databases
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return []
    
    def get_database_info(self, database_name: str) -> Dict[str, Any]:
        """Ottiene informazioni su un database"""
        try:
            # Ottieni lista tabelle
            query = f"SHOW TABLES FROM {database_name}"
            tables_result = self._execute_query(query, database=database_name)
            tables = [t.strip() for t in tables_result.split('\n') if t.strip()]
            
            # Calcola dimensioni totali (approssimativo)
            total_size = 0
            table_count = len(tables)
            
            # Prova a ottenere dimensioni tabelle
            for table in tables:
                try:
                    size_query = f"SELECT sum(bytes) FROM system.parts WHERE database = '{database_name}' AND table = '{table}' AND active = 1"
                    size_result = self._execute_query(size_query)
                    if size_result and size_result.isdigit():
                        total_size += int(size_result)
                except:
                    pass
            
            return {
                'name': database_name,
                'table_count': table_count,
                'tables': tables,
                'size_bytes': total_size,
                'size_mb': round(total_size / (1024 * 1024), 2) if total_size > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting database info for {database_name}: {e}")
            return {
                'name': database_name,
                'table_count': 0,
                'tables': [],
                'size_bytes': 0,
                'size_mb': 0,
                'error': str(e)
            }
    
    def create_database(self, database_name: str) -> Dict[str, Any]:
        """Crea un nuovo database"""
        try:
            # Valida nome database
            if not database_name or not database_name.replace('_', '').isalnum():
                return {
                    'success': False,
                    'error': 'Nome database non valido. Usa solo lettere, numeri e underscore'
                }
            
            # Verifica se esiste già
            query = f"SHOW DATABASES"
            existing = self._execute_query(query)
            if database_name in existing.split('\n'):
                return {
                    'success': False,
                    'error': f'Database "{database_name}" esiste già'
                }
            
            # Crea database
            create_query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
            self._execute_query(create_query)
            
            logger.info(f"Created ClickHouse database: {database_name}")
            return {
                'success': True,
                'message': f'Database "{database_name}" creato con successo'
            }
        except Exception as e:
            logger.error(f"Error creating database {database_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_database(self, database_name: str) -> Dict[str, Any]:
        """Elimina un database"""
        try:
            # Verifica che non sia un database di sistema
            if database_name in ['system', 'INFORMATION_SCHEMA', 'information_schema', 'default']:
                return {
                    'success': False,
                    'error': 'Non puoi eliminare database di sistema'
                }
            
            # Elimina database
            drop_query = f"DROP DATABASE IF EXISTS {database_name}"
            self._execute_query(drop_query)
            
            logger.info(f"Deleted ClickHouse database: {database_name}")
            return {
                'success': True,
                'message': f'Database "{database_name}" eliminato con successo'
            }
        except Exception as e:
            logger.error(f"Error deleting database {database_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_table_info(self, database_name: str, table_name: str) -> Dict[str, Any]:
        """Ottiene informazioni su una tabella"""
        try:
            # Ottieni schema
            schema_query = f"DESCRIBE TABLE {database_name}.{table_name}"
            schema_result = self._execute_query(schema_query, database=database_name)
            
            # Ottieni numero righe (approssimativo)
            count_query = f"SELECT count() FROM {database_name}.{table_name}"
            count_result = self._execute_query(count_query, database=database_name)
            row_count = int(count_result) if count_result.isdigit() else 0
            
            # Ottieni dimensioni
            size_query = f"SELECT sum(bytes) FROM system.parts WHERE database = '{database_name}' AND table = '{table_name}' AND active = 1"
            size_result = self._execute_query(size_query)
            size_bytes = int(size_result) if size_result and size_result.isdigit() else 0
            
            return {
                'name': table_name,
                'database': database_name,
                'row_count': row_count,
                'size_bytes': size_bytes,
                'size_mb': round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0,
                'schema': schema_result
            }
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {
                'name': table_name,
                'database': database_name,
                'error': str(e)
            }
    
    def preview_table(self, database_name: str, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Preview dati tabella (prime N righe)"""
        try:
            query = f"SELECT * FROM {database_name}.{table_name} LIMIT {limit}"
            result = self._execute_query(query, database=database_name)
            
            # Parse risultato (formato TSV)
            lines = result.split('\n')
            if not lines:
                return []
            
            # Prima riga = header
            headers = lines[0].split('\t')
            rows = []
            
            for line in lines[1:]:
                if not line.strip():
                    continue
                values = line.split('\t')
                row = dict(zip(headers, values))
                rows.append(row)
            
            return rows
        except Exception as e:
            logger.error(f"Error previewing table: {e}")
            return []
