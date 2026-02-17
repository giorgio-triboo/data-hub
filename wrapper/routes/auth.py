#!/usr/bin/env python3
"""
Auth Routes - Accesso diretto per rete interna (VPN). Nessun Google OAuth.
"""

import logging
from datetime import datetime
from flask import Blueprint, redirect, url_for, jsonify, render_template
from flask_login import login_user, logout_user, login_required, current_user
from services.auth_service import AuthService
from db import db
from models.user import User
from models.role import Role

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login():
    """Bypass: redirect immediato a accesso diretto (nessuna pagina login)."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.direct_login'))


@auth_bp.route('/direct')
def direct_login():
    """Accesso diretto: logga il primo admin. Solo rete interna (VPN)."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        return render_template('login.html', user=None, error='Nessun ruolo admin configurato.')
    user = User.query.filter_by(role_id=admin_role.id, is_active=True).first()
    if not user:
        return render_template('login.html', user=None, error='Nessun utente admin trovato.')
    user.last_login = datetime.utcnow()
    db.session.commit()
    login_user(user, remember=True)
    AuthService.log_action(user.id, user.email, 'login', resource_type='auth', details={'method': 'direct_internal'})
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout utente"""
    AuthService.log_action(
        current_user.id,
        current_user.email,
        'logout',
        resource_type='auth'
    )
    
    logout_user()
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/api/user')
@login_required
def get_current_user():
    """API per ottenere utente corrente"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'picture': current_user.picture,
        'role': {
            'id': current_user.role.id,
            'name': current_user.role.name,
            'description': current_user.role.description
        }
    })
