#!/usr/bin/env python3
"""
Airbyte Checker - Verifica stato di Airbyte gestito tramite abctl
Ottimizzato per evitare chiamate pesanti quando Airbyte è in crash
"""

import os
import subprocess
import logging
import requests
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AirbyteChecker:
    """Verifica stato di Airbyte gestito tramite abctl"""
    
    def __init__(self):
        self.airbyte_webapp_url = os.getenv('AIRBYTE_WEBAPP_URL', 'http://localhost:8000')
        self.abctl_available = self._check_abctl_available()
        
        # Cache per evitare chiamate troppo frequenti
        self._status_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 30  # Cache per 30 secondi
        
        # Traccia se Airbyte è in crash per evitare chiamate pesanti
        self._consecutive_failures = 0
        self._last_abctl_check = 0
        self._abctl_check_interval = 120  # Controlla abctl solo ogni 2 minuti se in crash
    
    def _check_abctl_available(self) -> bool:
        """Verifica se abctl è disponibile"""
        try:
            result = subprocess.run(
                ['abctl', '--version'],
                capture_output=True,
                timeout=3  # Timeout ridotto
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_airbyte_status(self) -> Dict[str, any]:
        """Verifica stato Airbyte tramite abctl e healthcheck"""
        # Usa cache se disponibile e valida
        current_time = time.time()
        if self._status_cache and (current_time - self._cache_timestamp) < self._cache_ttl:
            return self._status_cache
        
        # Prima verifica se abctl è disponibile
        if not self.abctl_available:
            result = {
                'status': 'disabled',
                'message': 'Airbyte not configured (abctl not available)'
            }
            self._update_cache(result)
            return result
        
        # Se abbiamo avuto molti fallimenti consecutivi, evita chiamate pesanti a abctl
        # e controlla solo l'healthcheck HTTP (più leggero)
        skip_abctl_check = (
            self._consecutive_failures >= 3 and 
            (current_time - self._last_abctl_check) < self._abctl_check_interval
        )
        
        if not skip_abctl_check:
            # Verifica se Airbyte è installato tramite abctl (solo se necessario)
            try:
                result = subprocess.run(
                    ['abctl', 'local', 'status'],
                    capture_output=True,
                    text=True,
                    timeout=5  # Timeout ridotto da 10 a 5 secondi
                )
                self._last_abctl_check = current_time
                
                # Se il comando fallisce, Airbyte non è installato
                if result.returncode != 0:
                    result = {
                        'status': 'disabled',
                        'message': 'Airbyte not installed (run: ./scripts/setup-airbyte.sh)'
                    }
                    self._update_cache(result)
                    return result
            except subprocess.TimeoutExpired:
                # Timeout significa che abctl è bloccato (probabilmente Airbyte in crash)
                logger.warning("abctl local status timeout - Airbyte may be in crash state")
                self._consecutive_failures += 1
                result = {
                    'status': 'unhealthy',
                    'message': 'Airbyte check timeout (may be in crash state)'
                }
                self._update_cache(result, ttl=60)  # Cache più lunga per stati di errore
                return result
            except FileNotFoundError:
                result = {
                    'status': 'disabled',
                    'message': 'Airbyte not configured'
                }
                self._update_cache(result)
                return result
            except Exception as e:
                logger.debug(f"Error checking abctl status: {e}")
                self._consecutive_failures += 1
        
        # Prova healthcheck HTTP (più leggero e veloce)
        # Nota: dall'interno del container, Airbyte potrebbe non essere raggiungibile
        # quindi proviamo prima con host.docker.internal, poi con localhost
        urls_to_try = [
            self.airbyte_webapp_url,  # Configurato (probabilmente host.docker.internal:8000)
            'http://host.docker.internal:8000',  # Fallback
            'http://localhost:8000'  # Ultimo tentativo
        ]
        
        for url in urls_to_try:
            try:
                response = requests.get(
                    f'{url}/api/v1/health',
                    timeout=2  # Timeout ridotto da 3 a 2 secondi
                )
                if response.status_code == 200:
                    # Successo: reset contatore fallimenti
                    self._consecutive_failures = 0
                    result = {
                        'status': 'healthy',
                        'message': 'Airbyte OK (managed by abctl)'
                    }
                    self._update_cache(result)
                    return result
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                continue
            except Exception as e:
                logger.debug(f"Error checking Airbyte at {url}: {e}")
                continue
        
        # Se nessun URL funziona, considera come unhealthy
        self._consecutive_failures += 1
        result = {
            'status': 'unhealthy',
            'message': 'Airbyte installed but not responding (check: abctl local status)'
        }
        # Cache più lunga per stati di errore per evitare polling eccessivo
        self._update_cache(result, ttl=60)
        return result
    
    def _update_cache(self, result: Dict, ttl: int = None):
        """Aggiorna cache con risultato"""
        self._status_cache = result
        self._cache_timestamp = time.time()
        if ttl:
            self._cache_ttl = ttl
    
    def get_airbyte_info(self) -> Dict[str, any]:
        """Ottiene informazioni su Airbyte"""
        info = {
            'managed_by': 'abctl',
            'webapp_url': self.airbyte_webapp_url,
            'abctl_available': self.abctl_available
        }
        
        if self.abctl_available:
            try:
                # Prova a ottenere versione
                result = subprocess.run(
                    ['abctl', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    info['abctl_version'] = result.stdout.strip()
            except Exception as e:
                logger.debug(f"Error getting abctl version: {e}")
        
        return info
