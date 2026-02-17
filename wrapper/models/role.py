#!/usr/bin/env python3
"""
Role Model - Modello ruolo
"""

from db import db


class Role(db.Model):
    """Modello ruolo con permessi"""
    
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    
    # Permessi come JSON (per flessibilità)
    permissions = db.Column(db.JSON, default=dict, nullable=False)
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se il ruolo ha un permesso specifico"""
        if not self.permissions:
            return False
        
        # Permessi gerarchici: admin ha tutto
        if self.name == 'admin':
            return True
        
        return self.permissions.get(permission, False)
    
    @staticmethod
    def get_default_roles():
        """Restituisce i ruoli di default"""
        return [
            {
                'name': 'admin',
                'description': 'Amministratore completo',
                'permissions': {
                    'view_healthcheck': True,
                    'manage_clickhouse': True,
                    'manage_airbyte': True,
                    'manage_users': True,
                    'view_audit_log': True,
                    'restart_services': True,
                }
            },
            {
                'name': 'developer',
                'description': 'Developer - può creare database e gestire servizi',
                'permissions': {
                    'view_healthcheck': True,
                    'manage_clickhouse': True,
                    'manage_airbyte': True,
                    'view_audit_log': True,
                    'restart_services': True,
                }
            },
            {
                'name': 'viewer',
                'description': 'Viewer - solo lettura',
                'permissions': {
                    'view_healthcheck': True,
                    'view_clickhouse': True,
                    'view_airbyte': True,
                }
            }
        ]
