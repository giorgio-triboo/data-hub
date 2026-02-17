#!/usr/bin/env python3
"""
Users Routes - Routes per gestione utenti
"""

import logging
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from services.auth_service import AuthService
from models.user import User
from models.role import Role
from db import db

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)


@users_bp.route('/users')
@login_required
def users_list():
    """Pagina lista utenti"""
    if not current_user.has_permission('manage_users'):
        return redirect(url_for('dashboard.index'))
    return render_template('users.html', user=current_user)


@users_bp.route('/api/users')
@login_required
def get_users():
    """API per ottenere lista utenti"""
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        users = AuthService.get_all_users()
        return jsonify({
            'success': True,
            'users': [{
                'id': u.id,
                'email': u.email,
                'name': u.name,
                'picture': u.picture,
                'role': {
                    'id': u.role.id,
                    'name': u.role.name,
                    'description': u.role.description
                },
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'last_login': u.last_login.isoformat() if u.last_login else None
            } for u in users]
        })
    except Exception as e:
        logger.error(f"Error getting users: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@users_bp.route('/api/users/<int:user_id>/role', methods=['PUT'])
@login_required
def update_user_role(user_id):
    """API per aggiornare ruolo utente"""
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        data = request.get_json()
        role_id = data.get('role_id')
        
        if not role_id:
            return jsonify({'error': 'role_id richiesto'}), 400
        
        success = AuthService.update_user_role(user_id, role_id)
        if success:
            # Log azione
            target_user = User.query.get(user_id)
            new_role = Role.query.get(role_id)
            AuthService.log_action(
                current_user.id,
                current_user.email,
                'update_user_role',
                resource_type='user',
                resource_id=str(user_id),
                details={
                    'target_user': target_user.email if target_user else None,
                    'new_role': new_role.name if new_role else None
                }
            )
            return jsonify({'success': True, 'message': 'Ruolo aggiornato con successo'})
        return jsonify({'error': 'Errore nell\'aggiornamento del ruolo'}), 500
    except Exception as e:
        logger.error(f"Error updating user role: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@users_bp.route('/api/users/<int:user_id>/toggle-active', methods=['PUT'])
@login_required
def toggle_user_active(user_id):
    """API per abilitare/disabilitare utente"""
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        # Non permettere di disabilitare se stessi
        if target_user.id == current_user.id:
            return jsonify({'error': 'Non puoi disabilitare il tuo stesso account'}), 400
        
        target_user.is_active = not target_user.is_active
        db.session.commit()
        
        # Log azione
        AuthService.log_action(
            current_user.id,
            current_user.email,
            'toggle_user_active',
            resource_type='user',
            resource_id=str(user_id),
            details={
                'target_user': target_user.email,
                'new_status': 'active' if target_user.is_active else 'inactive'
            }
        )
        
        return jsonify({
            'success': True,
            'is_active': target_user.is_active,
            'message': f'Utente {"abilitato" if target_user.is_active else "disabilitato"} con successo'
        })
    except Exception as e:
        logger.error(f"Error toggling user active: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/api/roles')
@login_required
def get_roles():
    """API per ottenere lista ruoli"""
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        roles = AuthService.get_all_roles()
        return jsonify({
            'success': True,
            'roles': [{
                'id': r.id,
                'name': r.name,
                'description': r.description
            } for r in roles]
        })
    except Exception as e:
        logger.error(f"Error getting roles: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
