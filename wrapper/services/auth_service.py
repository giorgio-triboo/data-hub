#!/usr/bin/env python3
"""
Auth Service - Servizio per autenticazione e gestione utenti
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from flask import request
from db import db
from models.user import User
from models.role import Role
from models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuthService:
    """Servizio per gestione autenticazione e utenti"""
    
    @staticmethod
    def get_or_create_user(google_id: str, email: str, name: str = None, picture: str = None) -> User:
        """Ottiene o crea un utente da dati Google OAuth"""
        # Prima cerca per Google ID
        user = User.query.filter_by(google_id=google_id).first()
        
        # Se non trovato, cerca per email (per gestire utente admin di default)
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                # Aggiorna Google ID se era un utente di default
                user.google_id = google_id
                db.session.commit()
                logger.info(f"Updated Google ID for existing user: {email}")
        
        if not user:
            # Crea nuovo utente con ruolo viewer di default
            default_role = Role.query.filter_by(name='viewer').first()
            if not default_role:
                # Se non esiste, crea ruolo viewer
                default_role = Role(name='viewer', description='Viewer - solo lettura', permissions={})
                db.session.add(default_role)
                db.session.commit()
            
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
                role_id=default_role.id
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user: {email}")
        else:
            # Aggiorna ultimo login
            user.last_login = datetime.utcnow()
            # Aggiorna dati se cambiati
            if name and user.name != name:
                user.name = name
            if picture and user.picture != picture:
                user.picture = picture
            db.session.commit()
        
        return user
    
    @staticmethod
    def check_allowed_domain(email: str, allowed_domains: list) -> bool:
        """Verifica se l'email appartiene a un dominio consentito"""
        if not allowed_domains:
            return True  # Nessuna restrizione
        
        domain = email.split('@')[1] if '@' in email else ''
        return domain in allowed_domains
    
    @staticmethod
    def log_action(user_id: Optional[int], user_email: str, action: str, 
                   resource_type: str = None, resource_id: str = None, 
                   details: Dict[str, Any] = None):
        """Registra un'azione nell'audit log"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=request.remote_addr if request else None
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging action: {e}", exc_info=True)
            db.session.rollback()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Ottiene utente per ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def update_user_role(user_id: int, role_id: int) -> bool:
        """Aggiorna ruolo utente"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            role = Role.query.get(role_id)
            if not role:
                return False
            
            user.role_id = role_id
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user role: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    @staticmethod
    def get_all_users():
        """Ottiene tutti gli utenti"""
        return User.query.order_by(User.created_at.desc()).all()
    
    @staticmethod
    def get_all_roles():
        """Ottiene tutti i ruoli"""
        return Role.query.all()
    
    @staticmethod
    def initialize_default_roles():
        """Inizializza ruoli di default se non esistono"""
        existing_roles = {r.name for r in Role.query.all()}
        default_roles = Role.get_default_roles()
        
        for role_data in default_roles:
            if role_data['name'] not in existing_roles:
                role = Role(
                    name=role_data['name'],
                    description=role_data['description'],
                    permissions=role_data['permissions']
                )
                db.session.add(role)
                logger.info(f"Created default role: {role_data['name']}")
        
        db.session.commit()
