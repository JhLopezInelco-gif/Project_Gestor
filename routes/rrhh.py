# -*- coding: utf-8 -*-
"""
Rutas del Módulo RRHH
- Panel de control: progreso de todos los empleados
- Estadísticas por área (capacitaciones vs aprobados/pendientes)
- Estadísticas por empleado (disponibles vs aprobadas)
- Filtros por área y estado
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from models import (db, Empleado, Capacitacion, ProgresoCapacitacion,
                    Area, User, Gestor, ReporteControl, CronogramaItem)

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


# ──────────────────────────────────────────────
#  REPORTES DE CONTROL FGH-22
# ──────────────────────────────────────────────
def _check_reporte_access():
    """Check if user can manage reportes (RRHH, Admin, Gestor)"""
    return current_user.role in ('RRHH', 'Admin', 'Gestor')


def _get_cronograma(reporte):
    """Split cronograma items into Section II and III"""
    if reporte:
        cronograma_ii = [c for c in reporte.cronograma if c.seccion == 'II']
        cronograma_iii = [c for c in reporte.cronograma if c.seccion == 'III']
    else:
        cronograma_ii = []
        cronograma_iii = []
    return cronograma_ii, cronograma_iii


def _save_cronograma(reporte_id, form, is_edit=False):
    """Save/update cronograma items from form data"""
    # Sección II: predefinidos
    for i, tema in enumerate(ReporteControl.TEMAS_PREDEFINIDOS):
        fecha_str = form.get(f'fecha_ii_{i}', '')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        entrenador = form.get(f'entrenador_ii_{i}', '').strip()
        firma = form.get(f'firma_ii_{i}', '').strip()

        if is_edit:
            item = CronogramaItem.query.filter_by(
                reporte_id=reporte_id, seccion='II', posicion=i
            ).first()
            if item:
                item.fecha_realizacion = fecha
                item.entrenador_asignado = entrenador
                item.firma_entrenador = firma
                continue

        db.session.add(CronogramaItem(
            reporte_id=reporte_id, seccion='II', posicion=i,
            tema=tema, fecha_realizacion=fecha,
            entrenador_asignado=entrenador, firma_entrenador=firma
        ))

    # Sección III: temas específicos (dinámicos)
    if is_edit:
        CronogramaItem.query.filter_by(
            reporte_id=reporte_id, seccion='III'
        ).delete()

    total_iii = form.get('total_filas_iii', 0, type=int)
    for i in range(total_iii):
        tema = form.get(f'tema_iii_{i}', '').strip()
        if not tema:
            continue
        fecha_str = form.get(f'fecha_iii_{i}', '')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        entrenador = form.get(f'entrenador_iii_{i}', '').strip()
        firma = form.get(f'firma_iii_{i}', '').strip()

        db.session.add(CronogramaItem(
            reporte_id=reporte_id, seccion='III', posicion=i,
            tema=tema, fecha_realizacion=fecha,
            entrenador_asignado=entrenador, firma_entrenador=firma
        ))


@rrhh_bp.route('/rrhh/reportes-control')
@login_required
def listar_reportes_control():
    if not _check_reporte_access():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    reportes = ReporteControl.query.order_by(
        ReporteControl.fecha_creacion.desc()
    ).all()
    return render_template('rrhh/listar_reportes.html', reportes=reportes)


@rrhh_bp.route('/rrhh/reportes-control/crear', methods=['GET', 'POST'])
@login_required
def crear_reporte_control():
    if not _check_reporte_access():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    empleados = Empleado.query.all()
    gestores = Gestor.query.all()

    if request.method == 'POST':
        empleado_id = request.form.get('empleado_id', type=int)
        fecha_str = request.form.get('fecha_ingreso', '')
        try:
            fecha_ingreso = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Fecha de ingreso inválida.', 'warning')
            return render_template('rrhh/reporte_control.html',
                                   reporte=None, empleados=empleados,
                                   gestores=gestores,
                                   cronograma_ii=[], cronograma_iii=[])

        # Auto-incrementar consecutivo
        ultimo = ReporteControl.query.order_by(
            ReporteControl.consecutivo.desc()
        ).first()
        consecutivo = (ultimo.consecutivo + 1) if ultimo else 1

        vinculacion = 'vinculacion' in request.form

        reporte = ReporteControl(
            consecutivo=consecutivo,
            empleado_id=empleado_id,
            nombres_apellidos=request.form.get('nombres_apellidos', '').strip(),
            fecha_ingreso=fecha_ingreso,
            cargo_desempenar=request.form.get('cargo_desempenar', '').strip(),
            vinculacion=vinculacion,
            dependencia=request.form.get('dependencia', '').strip(),
            estado='En Proceso',
            creado_por=current_user.id
        )
        db.session.add(reporte)
        db.session.flush()  # Obtener ID

        _save_cronograma(reporte.id, request.form)
        db.session.commit()

        flash(f'Reporte {reporte.codigo_completo} creado correctamente.', 'success')
        return redirect(url_for('rrhh.listar_reportes_control'))

    return render_template('rrhh/reporte_control.html',
                           reporte=None, empleados=empleados,
                           gestores=gestores,
                           cronograma_ii=[], cronograma_iii=[],
                           temas_predefinidos=ReporteControl.TEMAS_PREDEFINIDOS)


@rrhh_bp.route('/rrhh/reportes-control/<int:reporte_id>')
@login_required
def ver_reporte_control(reporte_id):
    if not _check_reporte_access():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    reporte = ReporteControl.query.get_or_404(reporte_id)
    cronograma_ii, cronograma_iii = _get_cronograma(reporte)
    return render_template('rrhh/ver_reporte.html',
                           reporte=reporte,
                           cronograma_ii=cronograma_ii,
                           cronograma_iii=cronograma_iii)


@rrhh_bp.route('/rrhh/reportes-control/<int:reporte_id>/editar',
               methods=['GET', 'POST'])
@login_required
def editar_reporte_control(reporte_id):
    if not _check_reporte_access():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    reporte = ReporteControl.query.get_or_404(reporte_id)
    gestores = Gestor.query.all()
    cronograma_ii, cronograma_iii = _get_cronograma(reporte)

    if request.method == 'POST':
        fecha_str = request.form.get('fecha_ingreso', '')
        try:
            reporte.fecha_ingreso = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Fecha inválida.', 'warning')
            return render_template('rrhh/reporte_control.html',
                                   reporte=reporte, empleados=[],
                                   gestores=gestores,
                                   cronograma_ii=cronograma_ii,
                                   cronograma_iii=cronograma_iii)

        reporte.nombres_apellidos = request.form.get('nombres_apellidos', '').strip()
        reporte.cargo_desempenar = request.form.get('cargo_desempenar', '').strip()
        reporte.vinculacion = 'vinculacion' in request.form
        reporte.dependencia = request.form.get('dependencia', '').strip()
        reporte.estado = request.form.get('estado', 'En Proceso')

        if reporte.estado == 'Aprobado' and not reporte.fecha_cierre:
            reporte.fecha_cierre = datetime.utcnow()

        # Delete old cronograma and save new
        CronogramaItem.query.filter_by(reporte_id=reporte.id).delete()
        _save_cronograma(reporte.id, request.form, is_edit=False)

        db.session.commit()
        flash(f'Reporte {reporte.codigo_completo} actualizado.', 'success')
        return redirect(url_for('rrhh.listar_reportes_control'))

    return render_template('rrhh/reporte_control.html',
                           reporte=reporte, empleados=[],
                           gestores=gestores,
                           cronograma_ii=cronograma_ii,
                           cronograma_iii=cronograma_iii)


@rrhh_bp.route('/rrhh/api/empleado/<int:empleado_id>/capacitaciones-aprobadas')
@login_required
def capacitaciones_aprobadas(empleado_id):
    """Retorna las capacitaciones aprobadas del empleado con tema, gestor y área."""
    if not _check_reporte_access():
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Buscar capacitaciones aprobadas del empleado
    progresos = ProgresoCapacitacion.query.filter(
        ProgresoCapacitacion.empleado_id == empleado_id,
        ProgresoCapacitacion.estado == 'Aprobado'
    ).all()

    capacitaciones_data = []
    gestores_vistos = set()

    for p in progresos:
        cap = Capacitacion.query.get(p.capacitacion_id)
        if not cap:
            continue
        gestor = Gestor.query.get(cap.gestor_id)
        if not gestor:
            continue

        user = User.query.get(gestor.user_id)
        area = Area.query.get(cap.area_id)

        nombre_gestor = user.nombre_completo if user else 'N/A'
        nombre_area = area.nombre_area if area else 'N/A'

        capacitaciones_data.append({
            'tema': cap.titulo,
            'gestor': nombre_gestor,
            'area': nombre_area,
            'fecha': p.fecha_completado.strftime('%Y-%m-%d') if p.fecha_completado else ''
        })

        # Registrar gestores únicos para el datalist
        gestores_vistos.add(nombre_gestor)

    return jsonify({
        'capacitaciones': capacitaciones_data,
        'gestores': list(gestores_vistos),
        'area_principal': capacitaciones_data[0]['area'] if capacitaciones_data else ''
    })


@rrhh_bp.route('/rrhh/reportes-control/<int:reporte_id>/eliminar',
               methods=['POST'])
@login_required
def eliminar_reporte_control(reporte_id):
    if current_user.role not in ('RRHH', 'Admin'):
        flash('Solo RRHH o Admin pueden eliminar reportes.', 'danger')
        return redirect(url_for('rrhh.listar_reportes_control'))

    reporte = ReporteControl.query.get_or_404(reporte_id)
    codigo = reporte.codigo_completo
    db.session.delete(reporte)
    db.session.commit()
    flash(f'Reporte {codigo} eliminado.', 'info')
    return redirect(url_for('rrhh.listar_reportes_control'))
