#!/usr/bin/env python3
"""
Routes - Flask routes
"""

from flask import Blueprint

def register_routes(app):
    """Registra tutte le routes (accesso solo interno/VPN, senza Google OAuth)"""
    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .healthcheck import healthcheck_bp
    from .clickhouse import clickhouse_bp
    from .airbyte import airbyte_bp
    from .users import users_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(healthcheck_bp)
    app.register_blueprint(clickhouse_bp)
    app.register_blueprint(airbyte_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(api_bp)
