#!/usr/bin/env python3
"""
Auth Routes - Routes per autenticazione Google OAuth
"""

import logging
from datetime import datetime
from flask import Blueprint, redirect, url_for, request, session, jsonify, current_app, render_template
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from config import Config
from services.auth_service import AuthService
from db import db

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Google OAuth blueprint sarà registrato in register_routes
def register_google_oauth(app):
    """Registra Google OAuth blueprint"""
    if Config.GOOGLE_OAUTH_CLIENT_ID and Config.GOOGLE_OAUTH_CLIENT_SECRET:
        # Flask-Dance costruisce automaticamente il redirect URI basandosi sull'URL dell'app
        # Per forzare l'URI esatto che corrisponde a Google Console, dobbiamo:
        # 1. Non usare redirect_to (che costruisce l'URI dinamicamente)
        # 2. Usare redirect_url con l'URI completo
        # 3. IMPORTANTE: Flask-Dance usa /authorized di default, ma noi abbiamo /callback
        #    Quindi dobbiamo disabilitare il callback automatico e gestirlo manualmente
        google_bp = make_google_blueprint(
            client_id=Config.GOOGLE_OAUTH_CLIENT_ID,
            client_secret=Config.GOOGLE_OAUTH_CLIENT_SECRET,
            authorized_url='/google/callback',  # Endpoint callback (Flask-Dance aggiunge /auth automaticamente)
            redirect_to='dashboard.index',  # Dove reindirizzare dopo login
            scope=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
        )
        # Registra il blueprint con prefix /auth
        # Con authorized_url='/auth/google/callback' crea la route: /auth/google/callback
        app.register_blueprint(google_bp, url_prefix='/auth')
        
        # Configura il callback personalizzato per match per email
        setup_google_oauth_callback(google_bp)


@auth_bp.route('/login')
def login():
    """Pagina di login con Google"""
    if not Config.GOOGLE_OAUTH_CLIENT_ID or not Config.GOOGLE_OAUTH_CLIENT_SECRET:
        return render_template('login.html', user=None, error='Google OAuth non configurato. Contatta l\'amministratore.')
    
    return render_template('login.html', user=current_user if current_user.is_authenticated else None)


# Usiamo il signal di Flask-Dance per intercettare il callback e gestire il login
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.consumer import OAuth2ConsumerBlueprint

def setup_google_oauth_callback(google_bp):
    """Configura il callback per gestire il login con match per email"""
    @oauth_authorized.connect_via(google_bp)
    def google_logged_in(blueprint, token):
        """Callback quando Google OAuth è completato"""
        if not token:
            logger.error("No token received from Google OAuth")
            return False
        
        try:
            # Ottieni informazioni utente da Google
            resp = google.get('/oauth2/v2/userinfo')
            if not resp.ok:
                logger.error(f"Google OAuth error: {resp.status_code} - {resp.text}")
                return False
            
            user_info = resp.json()
            google_id = user_info.get('id')
            email = user_info.get('email', '').lower().strip()  # Normalizza email
            name = user_info.get('name', '')
            picture = user_info.get('picture', '')
            
            if not email:
                logger.error("Email non ricevuta da Google OAuth")
                return False
            
            # Verifica dominio consentito
            if not AuthService.check_allowed_domain(email, Config.ALLOWED_GOOGLE_DOMAINS):
                logger.warning(f"Domain not allowed: {email}")
                return False
            
            # Cerca PRIMA per email nel database (priorità assoluta)
            from models.user import User
            user = User.query.filter_by(email=email).first()
            
            if user:
                # Utente trovato per email - aggiorna Google ID se necessario
                if user.google_id != google_id:
                    user.google_id = google_id
                    db.session.commit()
                    logger.info(f"Updated Google ID for existing user: {email}")
                
                # Aggiorna dati
                user.last_login = datetime.utcnow()
                if name and user.name != name:
                    user.name = name
                if picture and user.picture != picture:
                    user.picture = picture
                db.session.commit()
                
                logger.info(f"User found by email: {email}, role: {user.role.name}")
            else:
                # Utente non trovato - usa il metodo standard
                user = AuthService.get_or_create_user(google_id, email, name, picture)
            
            # Login
            login_user(user, remember=True)
            
            # Log azione
            AuthService.log_action(
                user.id,
                user.email,
                'login',
                resource_type='auth',
                details={'method': 'google_oauth', 'matched_by': 'email' if User.query.filter_by(email=email).first() else 'google_id'}
            )
            
            # Reindirizza alla dashboard (Flask-Dance farà il redirect)
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error in Google OAuth callback: {e}", exc_info=True)
            return False


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
