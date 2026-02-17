#!/usr/bin/env python3
"""
User Model - Modello utente
"""

from datetime import datetime
from flask_login import UserMixin
from db import db


class User(UserMixin, db.Model):
    """Modello utente con autenticazione Google"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=True)
    picture = db.Column(db.String(500), nullable=True)
    
    # Ruolo
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, default=1)
    role = db.relationship('Role', backref='users')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se l'utente ha un permesso specifico"""
        return self.role and self.role.has_permission(permission)
    
    def is_admin(self) -> bool:
        """Verifica se l'utente è admin"""
        return self.role and self.role.name == 'admin'
