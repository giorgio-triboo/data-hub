#!/usr/bin/env python3
"""
Audit Log Model - Modello audit log
"""

from datetime import datetime
from db import db


class AuditLog(db.Model):
    """Modello audit log per tracciare azioni utenti"""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Utente
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)  # Cache email per query veloci
    
    # Azione
    action = db.Column(db.String(100), nullable=False, index=True)  # es: 'create_database', 'delete_database', 'restart_service'
    resource_type = db.Column(db.String(50), nullable=True, index=True)  # es: 'clickhouse_database', 'service'
    resource_id = db.Column(db.String(255), nullable=True)  # es: nome database, nome servizio
    
    # Dettagli
    details = db.Column(db.JSON, nullable=True)  # Dettagli aggiuntivi in formato JSON
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_email} at {self.created_at}>'
    
    def to_dict(self):
        """Converte in dizionario per JSON"""
        return {
            'id': self.id,
            'user_email': self.user_email,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
