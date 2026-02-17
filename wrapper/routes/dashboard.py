#!/usr/bin/env python3
"""
Dashboard Routes - Routes principali dashboard
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Dashboard principale - redirect a login se non autenticato"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html', user=current_user)


@dashboard_bp.route('/healthcheck')
@login_required
def healthcheck():
    """Tab Healthcheck"""
    return render_template('healthcheck.html', user=current_user)


@dashboard_bp.route('/clickhouse')
@login_required
def clickhouse():
    """Tab ClickHouse"""
    if not current_user.has_permission('view_clickhouse') and not current_user.has_permission('manage_clickhouse'):
        return redirect(url_for('dashboard.index'))
    return render_template('clickhouse.html', user=current_user)


@dashboard_bp.route('/airbyte')
@login_required
def airbyte():
    """Tab Airbyte"""
    if not current_user.has_permission('view_airbyte') and not current_user.has_permission('manage_airbyte'):
        return redirect(url_for('dashboard.index'))
    return render_template('airbyte.html', user=current_user)
