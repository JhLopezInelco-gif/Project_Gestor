# -*- coding: utf-8 -*-
"""Rutas principales - Dashboard y navegación"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Capacitacion, ProgresoCapacitacion, Empleado, Documento, User, Gestor

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {}
    role = current_user.role

    if role == 'Admin':
        stats['total_capacitaciones'] = Capacitacion.query.filter_by(activa=True).count()
        stats['total_empleados'] = Empleado.query.count()
        stats['total_documentos'] = Documento.query.count()
        stats['total_usuarios'] = User.query.count()
        return render_template('dashboard/admin.html', stats=stats)

    elif role == 'Gestor':
        gestor = Gestor.query.filter_by(user_id=current_user.id).first()
        if gestor:
            stats['mis_capacitaciones'] = Capacitacion.query.filter_by(
                gestor_id=gestor.id, activa=True
            ).count()
            stats['mi_area'] = gestor.area.nombre_area
        return render_template('dashboard/gestor.html', stats=stats, gestor=gestor)

    elif role == 'Empleado':
        empleado = Empleado.query.filter_by(user_id=current_user.id).first()
        if empleado:
            stats['cursos_disponibles'] = Capacitacion.query.filter_by(activa=True).count()
            stats['cursos_completados'] = ProgresoCapacitacion.query.filter_by(
                empleado_id=empleado.id, estado='Aprobado'
            ).count()
            stats['cursos_pendientes'] = ProgresoCapacitacion.query.filter_by(
                empleado_id=empleado.id, estado='Pendiente'
            ).count()
        return render_template('dashboard/empleado.html', stats=stats, empleado=empleado)

    elif role == 'RRHH':
        stats['total_empleados'] = Empleado.query.count()
        stats['total_capacitaciones'] = Capacitacion.query.filter_by(activa=True).count()
        stats['aprobados'] = ProgresoCapacitacion.query.filter_by(estado='Aprobado').count()
        stats['pendientes'] = ProgresoCapacitacion.query.filter_by(estado='Pendiente').count()
        return render_template('dashboard/rrhh.html', stats=stats)

    return render_template('dashboard/base_dashboard.html', stats=stats)