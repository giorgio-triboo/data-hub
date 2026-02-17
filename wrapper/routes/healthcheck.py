#!/usr/bin/env python3
"""
Healthcheck Routes - API per monitoraggio servizi
"""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from service_monitor import ServiceMonitor
from airbyte_checker import AirbyteChecker

healthcheck_bp = Blueprint('healthcheck', __name__)

# Inizializza servizi
service_monitor = ServiceMonitor()
airbyte_checker = AirbyteChecker()


@healthcheck_bp.route('/api/healthcheck/status')
@login_required
def get_status():
    """API per ottenere stato di tutti i servizi"""
    if not current_user.has_permission('view_healthcheck'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        # Ottieni stato Airbyte
        airbyte_status = airbyte_checker.check_airbyte_status()
        
        # Ottieni stato tutti i servizi
        services = service_monitor.get_all_services_status(airbyte_status)
        
        healthy_count = sum(1 for s in services.values() if s.get('status') == 'healthy')
        total_count = len([s for s in services.values() if s.get('status') != 'disabled'])
        
        return jsonify({
            'timestamp': service_monitor.__class__.__module__ if hasattr(service_monitor, '__class__') else None,
            'overall_status': 'healthy' if healthy_count == total_count else 'unhealthy',
            'healthy_count': healthy_count,
            'total_count': total_count,
            'services': services
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@healthcheck_bp.route('/api/healthcheck/run')
@login_required
def run_healthcheck():
    """API per eseguire healthcheck manuale"""
    if not current_user.has_permission('view_healthcheck'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        airbyte_status = airbyte_checker.check_airbyte_status()
        is_healthy = service_monitor.run_healthcheck(airbyte_status)
        
        return jsonify({
            'success': True,
            'all_healthy': is_healthy
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
