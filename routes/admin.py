# -*- coding: utf-8 -*-
"""
Rutas del Módulo Administrador
- CRUD completo de Empleados
- CRUD completo de Gestores
Solo accesible por rol Admin
"""

from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from models import db, User, Empleado, Gestor, Area

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorador para verificar que el usuario sea Admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'Admin':
            flash('Acceso no autorizado. Solo administradores.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ═══════════════════════════════════════════════
#  CRUD EMPLEADOS
# ═══════════════════════════════════════════════

@admin_bp.route('/admin/empleados')
@login_required
@admin_required
def listar_empleados():
    """Listar todos los empleados"""
    empleados = Empleado.query.all()
    return render_template('admin/empleados/listar.html', empleados=empleados)


@admin_bp.route('/admin/empleados/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_empleado():
    """Crear un nuevo empleado (usuario + perfil empleado)"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        cargo = request.form.get('cargo', '').strip()
        fecha_ingreso = request.form.get('fecha_ingreso', '')

        # Validaciones
        if not all([username, password, nombres, apellidos, cargo]):
            flash('Todos los campos marcados con * son obligatorios.', 'warning')
            return render_template('admin/empleados/crear.html')

        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('admin/empleados/crear.html')

        # Crear usuario
        nuevo_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            nombres=nombres,
            apellidos=apellidos,
            role='Empleado',
            activo=True
        )
        db.session.add(nuevo_user)
        db.session.flush()

        # Crear perfil empleado
        fecha = datetime.strptime(fecha_ingreso, '%Y-%m-%d').date() if fecha_ingreso else datetime.utcnow().date()
        nuevo_empleado = Empleado(
            user_id=nuevo_user.id,
            cargo=cargo,
            fecha_ingreso=fecha
        )
        db.session.add(nuevo_empleado)
        db.session.commit()

        flash(f'Empleado "{nombres} {apellidos}" creado correctamente.', 'success')
        return redirect(url_for('admin.listar_empleados'))

    return render_template('admin/empleados/crear.html')


@admin_bp.route('/admin/empleados/<int:empleado_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_empleado(empleado_id):
    """Editar un empleado existente"""
    empleado = Empleado.query.get_or_404(empleado_id)
    user = empleado.user

    if request.method == 'POST':
        user.nombres = request.form.get('nombres', '').strip()
        user.apellidos = request.form.get('apellidos', '').strip()
        user.username = request.form.get('username', '').strip()
        empleado.cargo = request.form.get('cargo', '').strip()
        user.activo = 'activo' in request.form
        fecha_ingreso = request.form.get('fecha_ingreso', '')

        # Validar username único
        existing = User.query.filter_by(username=user.username).first()
        if existing and existing.id != user.id:
            flash('El nombre de usuario ya está en uso.', 'danger')
            return render_template('admin/empleados/editar.html', empleado=empleado)

        if fecha_ingreso:
            empleado.fecha_ingreso = datetime.strptime(fecha_ingreso, '%Y-%m-%d').date()

        # Cambiar contraseña si se proporciona
        new_password = request.form.get('new_password', '').strip()
        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash(f'Empleado "{user.nombre_completo}" actualizado correctamente.', 'success')
        return redirect(url_for('admin.listar_empleados'))

    return render_template('admin/empleados/editar.html', empleado=empleado)


@admin_bp.route('/admin/empleados/<int:empleado_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_empleado(empleado_id):
    """Eliminar un empleado y su usuario asociado"""
    empleado = Empleado.query.get_or_404(empleado_id)
    user = empleado.user
    nombre = user.nombre_completo

    # Eliminar progreso de capacitaciones
    from models import ProgresoCapacitacion
    ProgresoCapacitacion.query.filter_by(empleado_id=empleado.id).delete()

    db.session.delete(empleado)
    db.session.delete(user)
    db.session.commit()

    flash(f'Empleado "{nombre}" eliminado correctamente.', 'info')
    return redirect(url_for('admin.listar_empleados'))


# ═══════════════════════════════════════════════
#  CRUD GESTORES
# ═══════════════════════════════════════════════

@admin_bp.route('/admin/gestores')
@login_required
@admin_required
def listar_gestores():
    """Listar todos los gestores"""
    gestores = Gestor.query.all()
    return render_template('admin/gestores/listar.html', gestores=gestores)


@admin_bp.route('/admin/gestores/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_gestor():
    """Crear un nuevo gestor (usuario + perfil gestor)"""
    areas = Area.query.all()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        area_id = request.form.get('area_id', type=int)
        cargo = request.form.get('cargo', 'Gestor').strip()

        # Validaciones
        if not all([username, password, nombres, apellidos, area_id]):
            flash('Todos los campos marcados con * son obligatorios.', 'warning')
            return render_template('admin/gestores/crear.html', areas=areas)

        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('admin/gestores/crear.html', areas=areas)

        # Crear usuario
        nuevo_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            nombres=nombres,
            apellidos=apellidos,
            role='Gestor',
            activo=True
        )
        db.session.add(nuevo_user)
        db.session.flush()

        # Crear perfil gestor
        nuevo_gestor = Gestor(
            user_id=nuevo_user.id,
            area_id=area_id,
            cargo=cargo
        )
        db.session.add(nuevo_gestor)
        db.session.commit()

        flash(f'Gestor "{nombres} {apellidos}" creado correctamente.', 'success')
        return redirect(url_for('admin.listar_gestores'))

    return render_template('admin/gestores/crear.html', areas=areas)


@admin_bp.route('/admin/gestores/<int:gestor_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_gestor(gestor_id):
    """Editar un gestor existente"""
    gestor = Gestor.query.get_or_404(gestor_id)
    user = gestor.user
    areas = Area.query.all()

    if request.method == 'POST':
        user.nombres = request.form.get('nombres', '').strip()
        user.apellidos = request.form.get('apellidos', '').strip()
        user.username = request.form.get('username', '').strip()
        gestor.cargo = request.form.get('cargo', '').strip()
        gestor.area_id = request.form.get('area_id', type=int)
        user.activo = 'activo' in request.form

        # Validar username único
        existing = User.query.filter_by(username=user.username).first()
        if existing and existing.id != user.id:
            flash('El nombre de usuario ya está en uso.', 'danger')
            return render_template('admin/gestores/editar.html', gestor=gestor, areas=areas)

        # Cambiar contraseña si se proporciona
        new_password = request.form.get('new_password', '').strip()
        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash(f'Gestor "{user.nombre_completo}" actualizado correctamente.', 'success')
        return redirect(url_for('admin.listar_gestores'))

    return render_template('admin/gestores/editar.html', gestor=gestor, areas=areas)


@admin_bp.route('/admin/gestores/<int:gestor_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_gestor(gestor_id):
    """Eliminar un gestor y su usuario asociado"""
    gestor = Gestor.query.get_or_404(gestor_id)
    user = gestor.user
    nombre = user.nombre_completo

    # Verificar si tiene capacitaciones asignadas
    from models import Capacitacion
    caps = Capacitacion.query.filter_by(gestor_id=gestor.id).count()
    if caps > 0:
        flash(f'No se puede eliminar el gestor "{nombre}" porque tiene {caps} capacitación(es) asignada(s). '
              f'Reasigne o elimine las capacitaciones primero.', 'danger')
        return redirect(url_for('admin.listar_gestores'))

    db.session.delete(gestor)
    db.session.delete(user)
    db.session.commit()

    flash(f'Gestor "{nombre}" eliminado correctamente.', 'info')
    return redirect(url_for('admin.listar_gestores'))