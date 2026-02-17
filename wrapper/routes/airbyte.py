#!/usr/bin/env python3
"""
Airbyte Routes - API per gestione connessioni Airbyte
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.airbyte_service import AirbyteService
from services.auth_service import AuthService

airbyte_bp = Blueprint('airbyte', __name__)
airbyte_service = AirbyteService()


@airbyte_bp.route('/api/airbyte/status')
@login_required
def check_status():
    """API per verificare se Airbyte è raggiungibile"""
    if not current_user.has_permission('view_airbyte') and not current_user.has_permission('manage_airbyte'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        is_connected = airbyte_service.check_connection()
        return jsonify({
            'success': True,
            'connected': is_connected
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@airbyte_bp.route('/api/airbyte/connections')
@login_required
def list_connections():
    """API per listare tutte le connessioni"""
    if not current_user.has_permission('view_airbyte') and not current_user.has_permission('manage_airbyte'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        connections = airbyte_service.list_connections()
        return jsonify({
            'success': True,
            'connections': connections
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@airbyte_bp.route('/api/airbyte/connections/<connection_id>')
@login_required
def get_connection(connection_id):
    """API per ottenere dettagli di una connessione"""
    if not current_user.has_permission('view_airbyte') and not current_user.has_permission('manage_airbyte'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        connection = airbyte_service.get_connection_details(connection_id)
        if connection:
            return jsonify({
                'success': True,
                'connection': connection
            })
        return jsonify({'error': 'Connessione non trovata'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@airbyte_bp.route('/api/airbyte/connections/<connection_id>/sync', methods=['POST'])
@login_required
def trigger_sync(connection_id):
    """API per triggerare sync manuale"""
    if not current_user.has_permission('manage_airbyte'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        result = airbyte_service.trigger_sync(connection_id)
        
        if result.get('success'):
            # Log azione
            AuthService.log_action(
                current_user.id,
                current_user.email,
                'trigger_sync',
                resource_type='airbyte_connection',
                resource_id=connection_id
            )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@airbyte_bp.route('/api/airbyte/connections/<connection_id>/status')
@login_required
def get_connection_status(connection_id):
    """API per ottenere stato di una connessione"""
    if not current_user.has_permission('view_airbyte') and not current_user.has_permission('manage_airbyte'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        status = airbyte_service.get_connection_status(connection_id)
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@airbyte_bp.route('/api/airbyte/sources')
@login_required
def list_sources():
    """API per listare tutte le sources"""
    if not current_user.has_permission('view_airbyte') and not current_user.has_permission('manage_airbyte'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        sources = airbyte_service.list_sources()
        return jsonify({
            'success': True,
            'sources': sources
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@airbyte_bp.route('/api/airbyte/destinations')
@login_required
def list_destinations():
    """API per listare tutte le destinations"""
    if not current_user.has_permission('view_airbyte') and not current_user.has_permission('manage_airbyte'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        destinations = airbyte_service.list_destinations()
        return jsonify({
            'success': True,
            'destinations': destinations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
