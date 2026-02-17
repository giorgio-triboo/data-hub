#!/usr/bin/env python3
"""
SSE Manager - Gestione Server-Sent Events per aggiornamenti live
"""

import json
import queue
import logging
from datetime import datetime
from typing import List, Dict, Any
from flask import Response, stream_with_context

logger = logging.getLogger(__name__)


class SSEManager:
    """Gestisce connessioni Server-Sent Events"""
    
    def __init__(self):
        self.clients: List[queue.Queue] = []
    
    def add_client(self) -> queue.Queue:
        """Aggiunge un nuovo client SSE"""
        q = queue.Queue()
        self.clients.append(q)
        return q
    
    def remove_client(self, client_queue: queue.Queue):
        """Rimuove un client SSE"""
        if client_queue in self.clients:
            self.clients.remove(client_queue)
    
    def broadcast_event(self, event_data: Dict[str, Any]):
        """Invia evento a tutti i client SSE connessi"""
        for client_queue in self.clients[:]:  # Copia lista per evitare modifiche durante iterazione
            try:
                client_queue.put_nowait(event_data)
            except queue.Full:
                # Rimuovi client se coda piena
                self.remove_client(client_queue)
            except Exception as e:
                logger.error(f"Error broadcasting to SSE client: {e}")
                self.remove_client(client_queue)
    
    def create_event_stream(self):
        """Genera stream di eventi SSE"""
        q = self.add_client()
        
        try:
            # Invia evento iniziale
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE connection established'})}\n\n"
            
            while True:
                try:
                    # Attendi evento dalla coda (timeout 30 secondi per keepalive)
                    event = q.get(timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Keepalive
                    yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"
        except GeneratorExit:
            # Client disconnesso
            self.remove_client(q)
    
    def get_response(self):
        """Crea Response Flask per SSE"""
        return Response(
            stream_with_context(self.create_event_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
