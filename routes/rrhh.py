# -*- coding: utf-8 -*-
"""
Rutas del Módulo RRHH
- Panel de control: progreso de todos los empleados
- Tabla con cursos iniciados, completados y calificaciones
- Filtros por área y estado
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import (db, Empleado, Capacitacion, ProgresoCapacitacion,
                    Area, User)

rrhh_bp = Blueprint('rrhh', __name__)


@rrhh_bp.route('/rrhh/panel')
@login_required
def panel():
    if current_user.role not in ('RRHH', 'Admin'):
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Filtros
    area_id = request.args.get('area_id', type=int)
    estado_filtro = request.args.get('estado', '').strip()

    # Query base: todos los empleados
    empleados = Empleado.query.all()

    # Obtener todos los progresos con filtros opcionales
    progresos_query = ProgresoCapacitacion.query

    if estado_filtro in ('Aprobado', 'Pendiente'):
        progresos_query = progresos_query.filter_by(estado=estado_filtro)

    progresos = progresos_query.all()

    # Filtrar por área si se especifica
    if area_id:
        cap_ids = [c.id for c in Capacitacion.query.filter_by(area_id=area_id).all()]
        progresos = [p for p in progresos if p.capacitacion_id in cap_ids]

    # Construir tabla de datos
    tabla_empleados = []
    for empleado in empleados:
        user = User.query.get(empleado.user_id)
        emp_progresos = [p for p in progresos if p.empleado_id == empleado.id]

        total_cursos = len(emp_progresos)
        aprobados = sum(1 for p in emp_progresos if p.estado == 'Aprobado')
        pendientes = total_cursos - aprobados
        promedio = 0
        if emp_progresos:
            promedio = round(
                sum(p.calificacion for p in emp_progresos) / len(emp_progresos), 1
            )

        # Detalle de cada curso
        cursos_detalle = []
        for p in emp_progresos:
            cap = Capacitacion.query.get(p.capacitacion_id)
            cursos_detalle.append({
                'titulo': cap.titulo if cap else 'N/A',
                'area': cap.area.nombre_area if cap and cap.area else 'N/A',
                'calificacion': p.calificacion,
                'estado': p.estado,
                'fecha': p.fecha_completado.strftime('%d/%m/%Y %H:%M')
                         if p.fecha_completado else 'N/A'
            })

        tabla_empleados.append({
            'empleado_id': empleado.id,
            'nombre': user.nombre_completo if user else 'N/A',
            'username': user.username if user else 'N/A',
            'cargo': empleado.cargo,
            'total_cursos': total_cursos,
            'aprobados': aprobados,
            'pendientes': pendientes,
            'promedio': promedio,
            'cursos': cursos_detalle
        })

    # Estadísticas generales
    total_progresos = ProgresoCapacitacion.query.count()
    total_aprobados = ProgresoCapacitacion.query.filter_by(estado='Aprobado').count()
    total_pendientes = total_progresos - total_aprobados
    areas = Area.query.all()

    stats = {
        'total_empleados': len(empleados),
        'total_capacitaciones': Capacitacion.query.filter_by(activa=True).count(),
        'total_progresos': total_progresos,
        'total_aprobados': total_aprobados,
        'total_pendientes': total_pendientes,
        'tasa_aprobacion': round((total_aprobados / total_progresos * 100), 1)
                           if total_progresos > 0 else 0
    }

    return render_template('rrhh/panel.html',
                           tabla_empleados=tabla_empleados,
                           areas=areas,
                           stats=stats,
                           area_seleccionada=area_id,
                           estado_filtro=estado_filtro)


# ──────────────────────────────────────────────
#  VER DETALLE DE UN EMPLEADO
# ──────────────────────────────────────────────
@rrhh_bp.route('/rrhh/empleado/<int:empleado_id>')
@login_required
def detalle_empleado(empleado_id):
    if current_user.role not in ('RRHH', 'Admin'):
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    empleado = Empleado.query.get_or_404(empleado_id)
    user = User.query.get(empleado.user_id)

    progresos = ProgresoCapacitacion.query.filter_by(
        empleado_id=empleado.id
    ).order_by(ProgresoCapacitacion.fecha_completado.desc()).all()

    return render_template('rrhh/detalle_empleado.html',
                           empleado=empleado,
                           user=user,
                           progresos=progresos)


# ──────────────────────────────────────────────
#  REPORTE GENERAL
# ──────────────────────────────────────────────
@rrhh_bp.route('/rrhh/reporte')
@login_required
def reporte():
    if current_user.role not in ('RRHH', 'Admin'):
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Reporte por área
    areas = Area.query.all()
    reporte_areas = []

    for area in areas:
        caps = Capacitacion.query.filter_by(area_id=area.id, activa=True).all()
        cap_ids = [c.id for c in caps]
        total_progresos = ProgresoCapacitacion.query.filter(
            ProgresoCapacitacion.capacitacion_id.in_(cap_ids)
        ).count() if cap_ids else 0
        aprobados = ProgresoCapacitacion.query.filter(
            ProgresoCapacitacion.capacitacion_id.in_(cap_ids),
            ProgresoCapacitacion.estado == 'Aprobado'
        ).count() if cap_ids else 0

        reporte_areas.append({
            'area': area.nombre_area,
            'total_capacitaciones': len(caps),
            'total_progresos': total_progresos,
            'aprobados': aprobados,
            'pendientes': total_progresos - aprobados,
            'tasa': round((aprobados / total_progresos * 100), 1)
                    if total_progresos > 0 else 0
        })

    return render_template('rrhh/reporte.html', reporte_areas=reporte_areas)