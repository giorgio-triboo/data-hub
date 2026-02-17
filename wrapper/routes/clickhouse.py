#!/usr/bin/env python3
"""
ClickHouse Routes - API per gestione database ClickHouse
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.clickhouse_service import ClickHouseService
from services.auth_service import AuthService

clickhouse_bp = Blueprint('clickhouse', __name__)
clickhouse_service = ClickHouseService()


@clickhouse_bp.route('/api/clickhouse/databases')
@login_required
def list_databases():
    """API per listare tutti i database"""
    if not current_user.has_permission('view_clickhouse') and not current_user.has_permission('manage_clickhouse'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        databases = clickhouse_service.list_databases()
        return jsonify({
            'success': True,
            'databases': databases
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clickhouse_bp.route('/api/clickhouse/databases', methods=['POST'])
@login_required
def create_database():
    """API per creare un nuovo database"""
    if not current_user.has_permission('manage_clickhouse'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        data = request.get_json()
        database_name = data.get('name')
        
        if not database_name:
            return jsonify({'error': 'Nome database richiesto'}), 400
        
        result = clickhouse_service.create_database(database_name)
        
        if result.get('success'):
            # Log azione
            AuthService.log_action(
                current_user.id,
                current_user.email,
                'create_database',
                resource_type='clickhouse_database',
                resource_id=database_name
            )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clickhouse_bp.route('/api/clickhouse/databases/<database_name>', methods=['DELETE'])
@login_required
def delete_database(database_name):
    """API per eliminare un database"""
    if not current_user.has_permission('manage_clickhouse'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        result = clickhouse_service.delete_database(database_name)
        
        if result.get('success'):
            # Log azione
            AuthService.log_action(
                current_user.id,
                current_user.email,
                'delete_database',
                resource_type='clickhouse_database',
                resource_id=database_name
            )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clickhouse_bp.route('/api/clickhouse/databases/<database_name>/info')
@login_required
def get_database_info(database_name):
    """API per ottenere info su un database"""
    if not current_user.has_permission('view_clickhouse') and not current_user.has_permission('manage_clickhouse'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        info = clickhouse_service.get_database_info(database_name)
        return jsonify({
            'success': True,
            'database': info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clickhouse_bp.route('/api/clickhouse/databases/<database_name>/tables/<table_name>/info')
@login_required
def get_table_info(database_name, table_name):
    """API per ottenere info su una tabella"""
    if not current_user.has_permission('view_clickhouse') and not current_user.has_permission('manage_clickhouse'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        info = clickhouse_service.get_table_info(database_name, table_name)
        return jsonify({
            'success': True,
            'table': info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clickhouse_bp.route('/api/clickhouse/databases/<database_name>/tables/<table_name>/preview')
@login_required
def preview_table(database_name, table_name):
    """API per preview dati tabella"""
    if not current_user.has_permission('view_clickhouse') and not current_user.has_permission('manage_clickhouse'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        limit = request.args.get('limit', 100, type=int)
        rows = clickhouse_service.preview_table(database_name, table_name, limit)
        return jsonify({
            'success': True,
            'rows': rows,
            'limit': limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clickhouse_bp.route('/clickhouse/databases/<database_name>')
@login_required
def database_detail(database_name):
    """Vista dettagli database"""
    if not current_user.has_permission('view_clickhouse') and not current_user.has_permission('manage_clickhouse'):
        from flask import redirect, url_for
        return redirect(url_for('dashboard.index'))
    
    from flask import render_template
    return render_template('database_detail.html', user=current_user, database_name=database_name)
