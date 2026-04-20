# -*- coding: utf-8 -*-
"""Rutas de autenticación - Login/Logout con roles"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Usuario no encontrado.', 'danger')
            return render_template('auth/login.html')

        if not check_password_hash(user.password_hash, password):
            flash('Contraseña incorrecta.', 'danger')
            return render_template('auth/login.html')

        if not user.activo:
            flash('Su cuenta está desactivada. Contacte al administrador.', 'warning')
            return render_template('auth/login.html')

        login_user(user, remember=True)
        flash(f'Bienvenido, {user.nombre_completo}!', 'success')

        # Redirigir según rol
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))