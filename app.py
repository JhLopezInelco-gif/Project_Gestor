# -*- coding: utf-8 -*-
"""
Aplicación Principal - Gestor de Documentación y Capacitación
-------------------------------------------------------------
Aplicación empresarial para gestión de documentación y capacitación.
Roles: Admin, Gestor, Empleado, RRHH
"""

import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicie sesión para acceder.'
login_manager.login_message_category = 'warning'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # Crear carpeta de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Registrar Blueprints
    from routes import register_blueprints
    register_blueprints(app)

    # Crear tablas de base de datos
    with app.app_context():
        db.create_all()

    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Filtro de Jinja para mostrar nombres de roles
    @app.template_filter('role_label')
    def role_label(role):
        labels = {
            'Admin': 'Administrador',
            'Gestor': 'Gestor',
            'Empleado': 'Empleado',
            'RRHH': 'Recursos Humanos'
        }
        return labels.get(role, role)

    @app.template_filter('role_badge')
    def role_badge(role):
        badges = {
            'Admin': 'bg-danger',
            'Gestor': 'bg-primary',
            'Empleado': 'bg-success',
            'RRHH': 'bg-info'
        }
        return badges.get(role, 'bg-secondary')

    @app.template_filter('estado_badge')
    def estado_badge(estado):
        if estado == 'Aprobado':
            return 'bg-success'
        return 'bg-warning text-dark'

    return app


# ──────────────────────────────────────────────
#  Punto de entrada
# ──────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)