#!/usr/bin/env python3
"""
Airbyte Service - Servizio per gestione connessioni Airbyte
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)


class AirbyteService:
    """Servizio per gestione connessioni Airbyte"""
    
    def __init__(self):
        self.api_url = Config.AIRBYTE_API_URL
        self.webapp_url = Config.AIRBYTE_WEBAPP_URL
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Esegue una richiesta all'API Airbyte"""
        try:
            url = f"{self.api_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return None
            
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.ConnectionError:
            logger.warning(f"Cannot connect to Airbyte API at {self.api_url}")
            return None
        except Exception as e:
            logger.error(f"Error making Airbyte API request: {e}")
            return None
    
    def check_connection(self) -> bool:
        """Verifica se Airbyte è raggiungibile"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """Lista tutte le connessioni"""
        try:
            result = self._make_request('GET', '/connections')
            if result and 'data' in result:
                connections = []
                for conn in result['data']:
                    conn_info = self.get_connection_details(conn.get('connectionId'))
                    if conn_info:
                        connections.append(conn_info)
                return connections
            return []
        except Exception as e:
            logger.error(f"Error listing connections: {e}")
            return []
    
    def get_connection_details(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Ottiene dettagli di una connessione"""
        try:
            # Ottieni info connessione
            conn_result = self._make_request('GET', f'/connections/{connection_id}')
            if not conn_result:
                return None
            
            # Ottieni source
            source_id = conn_result.get('sourceId')
            source_info = None
            if source_id:
                source_result = self._make_request('GET', f'/sources/{source_id}')
                if source_result:
                    source_info = {
                        'id': source_result.get('sourceId'),
                        'name': source_result.get('name'),
                        'sourceDefinitionId': source_result.get('sourceDefinitionId')
                    }
            
            # Ottieni destination
            destination_id = conn_result.get('destinationId')
            destination_info = None
            if destination_id:
                dest_result = self._make_request('GET', f'/destinations/{destination_id}')
                if dest_result:
                    destination_info = {
                        'id': dest_result.get('destinationId'),
                        'name': dest_result.get('name'),
                        'destinationDefinitionId': dest_result.get('destinationDefinitionId')
                    }
            
            # Ottieni ultimo job
            job_result = self._make_request('GET', f'/jobs?connectionId={connection_id}&limit=1')
            last_job = None
            if job_result and 'data' in job_result and job_result['data']:
                last_job = job_result['data'][0]
            
            return {
                'connection_id': connection_id,
                'name': conn_result.get('name', 'Unnamed'),
                'status': conn_result.get('status', 'unknown'),
                'schedule': conn_result.get('schedule', {}),
                'source': source_info,
                'destination': destination_info,
                'last_sync': last_job.get('createdAt') if last_job else None,
                'last_sync_status': last_job.get('status') if last_job else None
            }
        except Exception as e:
            logger.error(f"Error getting connection details: {e}")
            return None
    
    def trigger_sync(self, connection_id: str) -> Dict[str, Any]:
        """Triggera una sync manuale"""
        try:
            result = self._make_request('POST', f'/connections/{connection_id}/sync')
            if result:
                return {
                    'success': True,
                    'message': 'Sync avviata con successo',
                    'job_id': result.get('jobId')
                }
            return {
                'success': False,
                'error': 'Impossibile avviare sync'
            }
        except Exception as e:
            logger.error(f"Error triggering sync: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_connection_status(self, connection_id: str) -> Dict[str, Any]:
        """Ottiene stato di una connessione"""
        try:
            # Ottieni ultimi job
            job_result = self._make_request('GET', f'/jobs?connectionId={connection_id}&limit=5')
            
            if job_result and 'data' in job_result:
                jobs = job_result['data']
                if jobs:
                    last_job = jobs[0]
                    return {
                        'status': last_job.get('status', 'unknown'),
                        'last_sync': last_job.get('createdAt'),
                        'last_sync_duration': last_job.get('duration'),
                        'records_synced': last_job.get('recordsSynced', 0)
                    }
            
            return {
                'status': 'unknown',
                'last_sync': None
            }
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def list_sources(self) -> List[Dict[str, Any]]:
        """Lista tutte le sources"""
        try:
            result = self._make_request('GET', '/sources')
            if result and 'data' in result:
                return result['data']
            return []
        except Exception as e:
            logger.error(f"Error listing sources: {e}")
            return []
    
    def list_destinations(self) -> List[Dict[str, Any]]:
        """Lista tutte le destinations"""
        try:
            result = self._make_request('GET', '/destinations')
            if result and 'data' in result:
                return result['data']
            return []
        except Exception as e:
            logger.error(f"Error listing destinations: {e}")
            return []
