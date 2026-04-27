# -*- coding: utf-8 -*-
"""
Rutas del Módulo RRHH
- Panel de control: progreso de todos los empleados
- Estadísticas por área (capacitaciones vs aprobados/pendientes)
- Estadísticas por empleado (disponibles vs aprobadas)
- Filtros por área y estado
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import (db, Empleado, Capacitacion, ProgresoCapacitacion,
                    Area, User, Gestor)

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

    areas = Area.query.all()
    empleados = Empleado.query.all()
    todas_caps = Capacitacion.query.filter_by(activa=True).all()

    # ──────────────────────────────────────
    #  ESTADÍSTICAS POR ÁREA
    # ──────────────────────────────────────
    stats_areas = []
    for area in areas:
        caps_area = [c for c in todas_caps if c.area_id == area.id]
        cap_ids = [c.id for c in caps_area]

        total_progresos = 0
        aprobados = 0
        pendientes = 0

        if cap_ids:
            total_progresos = ProgresoCapacitacion.query.filter(
                ProgresoCapacitacion.capacitacion_id.in_(cap_ids)
            ).count()
            aprobados = ProgresoCapacitacion.query.filter(
                ProgresoCapacitacion.capacitacion_id.in_(cap_ids),
                ProgresoCapacitacion.estado == 'Aprobado'
            ).count()
            pendientes = total_progresos - aprobados

        tasa = round((aprobados / total_progresos * 100), 1) if total_progresos > 0 else 0

        # Gestores del área
        gestores_area = Gestor.query.filter_by(area_id=area.id).all()
        nombres_gestores = []
        for g in gestores_area:
            u = User.query.get(g.user_id)
            if u:
                nombres_gestores.append(u.nombre_completo)

        stats_areas.append({
            'area': area.nombre_area,
            'area_id': area.id,
            'total_capacitaciones': len(caps_area),
            'total_progresos': total_progresos,
            'aprobados': aprobados,
            'pendientes': pendientes,
            'tasa': tasa,
            'gestores': nombres_gestores
        })

    # ──────────────────────────────────────
    #  TABLA POR EMPLEADO (con filtros)
    # ──────────────────────────────────────
    # Capacitaciones filtradas por área
    caps_filtradas = todas_caps
    if area_id:
        caps_filtradas = [c for c in todas_caps if c.area_id == area_id]

    caps_filtradas_ids = [c.id for c in caps_filtradas]

    tabla_empleados = []
    for empleado in empleados:
        user = User.query.get(empleado.user_id)
        if not user:
            continue

        # Total capacitaciones disponibles para este empleado
        total_disponibles = len(caps_filtradas)

        # Progresos del empleado en las capacitaciones filtradas
        if caps_filtradas_ids:
            progresos_emp = ProgresoCapacitacion.query.filter(
                ProgresoCapacitacion.empleado_id == empleado.id,
                ProgresoCapacitacion.capacitacion_id.in_(caps_filtradas_ids)
            ).all()
        else:
            progresos_emp = []

        # Aplicar filtro de estado
        if estado_filtro in ('Aprobado', 'Pendiente'):
            progresos_emp = [p for p in progresos_emp if p.estado == estado_filtro]

        aprobados = sum(1 for p in progresos_emp if p.estado == 'Aprobado')
        pendientes = sum(1 for p in progresos_emp if p.estado == 'Pendiente')
        total_realizados = len(progresos_emp)

        # No mostrar empleado si no tiene resultados con los filtros
        if estado_filtro and total_realizados == 0 and area_id:
            continue

        promedio = 0
        if progresos_emp:
            promedio = round(
                sum(p.calificacion for p in progresos_emp) / len(progresos_emp), 1
            )

        # Porcentaje de aprobación vs disponibles
        pct_aprobacion = round((aprobados / total_disponibles * 100), 1) if total_disponibles > 0 else 0

        # Detalle de cursos
        cursos_detalle = []
        for p in progresos_emp:
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
            'nombre': user.nombre_completo,
            'username': user.username,
            'cargo': empleado.cargo,
            'total_disponibles': total_disponibles,
            'total_realizados': total_realizados,
            'aprobados': aprobados,
            'pendientes': pendientes,
            'promedio': promedio,
            'pct_aprobacion': pct_aprobacion,
            'cursos': cursos_detalle
        })

    # ──────────────────────────────────────
    #  ESTADÍSTICAS GENERALES (globales, no filtradas)
    # ──────────────────────────────────────
    total_progresos_global = ProgresoCapacitacion.query.count()
    total_aprobados_global = ProgresoCapacitacion.query.filter_by(estado='Aprobado').count()
    total_pendientes_global = total_progresos_global - total_aprobados_global

    stats = {
        'total_empleados': len(empleados),
        'total_capacitaciones': len(todas_caps),
        'total_progresos': total_progresos_global,
        'total_aprobados': total_aprobados_global,
        'total_pendientes': total_pendientes_global,
        'tasa_aprobacion': round((total_aprobados_global / total_progresos_global * 100), 1)
                           if total_progresos_global > 0 else 0
    }

    return render_template('rrhh/panel.html',
                           tabla_empleados=tabla_empleados,
                           areas=areas,
                           stats=stats,
                           stats_areas=stats_areas,
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

    # Todas las capacitaciones activas
    todas_caps = Capacitacion.query.filter_by(activa=True).all()
    caps_con_progreso = [p.capacitacion_id for p in progresos]
    caps_pendientes = [c for c in todas_caps if c.id not in caps_con_progreso]

    return render_template('rrhh/detalle_empleado.html',
                           empleado=empleado,
                           user=user,
                           progresos=progresos,
                           caps_pendientes=caps_pendientes,
                           total_disponibles=len(todas_caps))


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