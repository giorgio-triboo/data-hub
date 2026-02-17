#!/usr/bin/env python3
"""
DataHub Wrapper Application - Main Entry Point
"""

import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_dance.contrib.google import make_google_blueprint

from config import Config
from db import db
from models.user import User
from models.role import Role
from services.auth_service import AuthService
from routes import register_routes

# ============================================================================
# Configurazione Logging
# ============================================================================

log_level = Config.LOG_LEVEL
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/wrapper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# Flask Application
# ============================================================================

app = Flask(__name__)
app.config.from_object(Config)

# ============================================================================
# Database Setup
# ============================================================================

db.init_app(app)

# ============================================================================
# Flask-Login Setup
# ============================================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Carica utente per Flask-Login"""
    return User.query.get(int(user_id))


# ============================================================================
# Google OAuth Setup (registered in routes/auth.py)
# ============================================================================

if Config.GOOGLE_OAUTH_CLIENT_ID and Config.GOOGLE_OAUTH_CLIENT_SECRET:
    logger.info("Google OAuth configured")
else:
    logger.warning("Google OAuth not configured - set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET")


# ============================================================================
# Register Routes
# ============================================================================

register_routes(app)


# ============================================================================
# Database Initialization
# ============================================================================

def init_database():
    """Inizializza database e crea tabelle se non esistono"""
    with app.app_context():
        # Crea tutte le tabelle
        db.create_all()
        
        # Inizializza ruoli di default
        AuthService.initialize_default_roles()
        
        # Crea utente admin di default se non esiste
        create_default_admin()
        
        logger.info("Database initialized")


def create_default_admin():
    """Crea utente admin di default"""
    from models.user import User
    from models.role import Role
    
    default_admin_email = 'giorgio.contarini@triboo.it'
    
    # Ottieni ruolo admin
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        logger.error("Admin role not found, cannot create default admin")
        return
    
    # Verifica se l'utente esiste già
    existing_user = User.query.filter_by(email=default_admin_email).first()
    if existing_user:
        # Se esiste, assicurati che sia admin e attivo
        if existing_user.role_id != admin_role.id:
            existing_user.role_id = admin_role.id
            logger.info(f"Updated {default_admin_email} to admin role")
        if not existing_user.is_active:
            existing_user.is_active = True
            logger.info(f"Activated {default_admin_email}")
        db.session.commit()
        logger.info(f"Default admin user verified: {default_admin_email}")
        return
    
    # Crea utente admin (con Google ID temporaneo che verrà aggiornato al primo login)
    admin_user = User(
        google_id=f'seed_admin_{default_admin_email.replace("@", "_at_")}',
        email=default_admin_email,
        name='Giorgio Contarini',
        role_id=admin_role.id,
        is_active=True
    )
    
    try:
        db.session.add(admin_user)
        db.session.commit()
        logger.info(f"Created default admin user: {default_admin_email}")
        logger.info(f"  Google ID temporaneo: {admin_user.google_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default admin: {e}", exc_info=True)


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handler per 404"""
    return {'error': 'Not found'}, 404


@app.errorhandler(500)
def internal_error(error):
    """Handler per 500"""
    db.session.rollback()
    return {'error': 'Internal server error'}, 500


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Inizializza database
    init_database()
    
    # Avvia applicazione
    logger.info("=" * 70)
    logger.info("DataHub Wrapper Application Starting")
    logger.info(f"Port: {Config.WRAPPER_PORT}")
    logger.info(f"Log level: {log_level}")
    logger.info("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=Config.WRAPPER_PORT,
        debug=False,
        threaded=True
    )
