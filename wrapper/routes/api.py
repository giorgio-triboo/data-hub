#!/usr/bin/env python3
"""
API Routes - API generali
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.auth_service import AuthService
from models.audit_log import AuditLog
from db import db

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/audit-log')
@login_required
def get_audit_log():
    """API per ottenere audit log"""
    if not current_user.has_permission('view_audit_log'):
        return jsonify({'error': 'Permesso negato'}), 403
    
    try:
        limit = request.args.get('limit', 100, type=int)
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
