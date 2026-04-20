# -*- coding: utf-8 -*-
"""Registro de todos los Blueprints de rutas"""

from routes.auth import auth_bp
from routes.main import main_bp
from routes.gestor import gestor_bp
from routes.empleado import empleado_bp
from routes.rrhh import rrhh_bp
from routes.documentos import documentos_bp
from routes.admin import admin_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(gestor_bp)
    app.register_blueprint(empleado_bp)
    app.register_blueprint(rrhh_bp)
    app.register_blueprint(documentos_bp)
    app.register_blueprint(admin_bp)
