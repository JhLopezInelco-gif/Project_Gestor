# -*- coding: utf-8 -*-
"""
Rutas del Módulo Empleado
- Buscador de capacitaciones por área
- Visualizador de material de apoyo
- Sistema de evaluación: cuestionario con calificación automática
  Aprobado solo si Calificación >= 80%
"""

from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, jsonify, send_from_directory, current_app)
from flask_login import login_required, current_user
from datetime import datetime
import json
from models import (db, Empleado, Capacitacion, Pregunta,
                    ProgresoCapacitacion, Area, MaterialCapacitacion)

empleado_bp = Blueprint('empleado', __name__)


def get_empleado():
    """Obtener el perfil de empleado del usuario actual"""
    return Empleado.query.filter_by(user_id=current_user.id).first()


# ──────────────────────────────────────────────
#  BUSCADOR DE CAPACITACIONES POR ÁREA
# ──────────────────────────────────────────────
@empleado_bp.route('/capacitaciones')
@login_required
def listar_capacitaciones():
    if current_user.role != 'Empleado':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    empleado = get_empleado()
    if not empleado:
        flash('Perfil de empleado no encontrado.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Filtro por área
    area_id = request.args.get('area_id', type=int)
    buscar = request.args.get('buscar', '').strip()

    query = Capacitacion.query.filter_by(activa=True)

    if area_id:
        query = query.filter_by(area_id=area_id)
    if buscar:
        query = query.filter(Capacitacion.titulo.ilike(f'%{buscar}%'))

    capacitaciones = query.order_by(Capacitacion.fecha_creacion.desc()).all()
    areas = Area.query.all()

    # Obtener el progreso del empleado para cada capacitación
    progresos = {}
    for cap in capacitaciones:
        progreso = ProgresoCapacitacion.query.filter_by(
            empleado_id=empleado.id,
            capacitacion_id=cap.id
        ).first()
        progresos[cap.id] = progreso

    return render_template('empleado/listar_capacitaciones.html',
                           capacitaciones=capacitaciones,
                           areas=areas,
                           progresos=progresos,
                           area_seleccionada=area_id,
                           buscar=buscar,
                           empleado=empleado)


# ──────────────────────────────────────────────
#  VER MATERIAL DE APOYO
# ──────────────────────────────────────────────
@empleado_bp.route('/capacitacion/<int:capacitacion_id>/material')
@login_required
def ver_material(capacitacion_id):
    if current_user.role != 'Empleado':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    empleado = get_empleado()
    cap = Capacitacion.query.get_or_404(capacitacion_id)

    # Verificar si ya existe un registro de progreso
    progreso = ProgresoCapacitacion.query.filter_by(
        empleado_id=empleado.id,
        capacitacion_id=cap.id
    ).first()

    return render_template('empleado/ver_material.html',
                           capacitacion=cap,
                           progreso=progreso,
                           empleado=empleado)


# ──────────────────────────────────────────────
#  INICIAR / RENDERIZAR CUESTIONARIO
# ──────────────────────────────────────────────
@empleado_bp.route('/capacitacion/<int:capacitacion_id>/evaluacion',
                   methods=['GET'])
@login_required
def rendir_evaluacion(capacitacion_id):
    if current_user.role != 'Empleado':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    empleado = get_empleado()
    cap = Capacitacion.query.get_or_404(capacitacion_id)
    preguntas = Pregunta.query.filter_by(capacitacion_id=cap.id).all()

    if not preguntas:
        flash('Esta capacitación aún no tiene preguntas configuradas.',
              'warning')
        return redirect(url_for('empleado.ver_material',
                                capacitacion_id=cap.id))

    # Verificar si ya aprobó
    progreso = ProgresoCapacitacion.query.filter_by(
        empleado_id=empleado.id,
        capacitacion_id=cap.id
    ).first()

    if progreso and progreso.estado == 'Aprobado':
        flash(f'Ya aprobó esta capacitación con {progreso.calificacion}%.', 'info')
        return redirect(url_for('empleado.listar_capacitaciones'))

    return render_template('empleado/evaluacion.html',
                           capacitacion=cap,
                           preguntas=preguntas,
                           empleado=empleado)


# ──────────────────────────────────────────────
#  PROCESAR RESPUESTAS Y CALIFICAR
#  Lógica: resultado = (correctas / total) * 100
#  Aprobado solo si >= 80%
# ──────────────────────────────────────────────
@empleado_bp.route('/capacitacion/<int:capacitacion_id>/calificar',
                   methods=['POST'])
@login_required
def calificar_evaluacion(capacitacion_id):
    if current_user.role != 'Empleado':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    empleado = get_empleado()
    cap = Capacitacion.query.get_or_404(capacitacion_id)
    preguntas = Pregunta.query.filter_by(capacitacion_id=cap.id).all()

    if not preguntas:
        flash('No hay preguntas para evaluar.', 'warning')
        return redirect(url_for('empleado.listar_capacitaciones'))

    # Recoger respuestas del formulario
    respuestas_dadas = {}
    for pregunta in preguntas:
        respuesta = request.form.get(f'pregunta_{pregunta.id}', '')
        respuestas_dadas[str(pregunta.id)] = respuesta

    # ─── Calcular calificación ───
    # resultado = (respuestas_correctas / total_preguntas) * 100
    calificacion = ProgresoCapacitacion.calcular_calificacion(
        respuestas_dadas, preguntas
    )
    # Usar el porcentaje de aprobación definido por el gestor
    porcentaje_req = cap.porcentaje_aprobacion or 80
    estado = ProgresoCapacitacion.determinar_estado(
        calificacion, porcentaje_req
    )

    # Calcular detalle para mostrar
    correctas = 0
    total = len(preguntas)
    for pregunta in preguntas:
        if respuestas_dadas.get(str(pregunta.id), '').upper() == \
                pregunta.respuesta_correcta.upper():
            correctas += 1

    # Guardar o actualizar progreso
    progreso = ProgresoCapacitacion.query.filter_by(
        empleado_id=empleado.id,
        capacitacion_id=cap.id
    ).first()

    if progreso:
        # Si ya tenía un intento pendiente, actualizar con nueva calificación
        progreso.calificacion = calificacion
        progreso.estado = estado
        progreso.fecha_completado = datetime.utcnow()
        progreso.respuestas_json = json.dumps(respuestas_dadas)
    else:
        progreso = ProgresoCapacitacion(
            empleado_id=empleado.id,
            capacitacion_id=cap.id,
            calificacion=calificacion,
            estado=estado,
            fecha_completado=datetime.utcnow(),
            respuestas_json=json.dumps(respuestas_dadas)
        )
        db.session.add(progreso)

    db.session.commit()

    # Mensaje según resultado
    if estado == 'Aprobado':
        flash(
            f'¡Felicidades! Aprobó con {calificacion}% '
            f'({correctas}/{total} correctas).',
            'success'
        )
    else:
        flash(
            f'No aprobó. Calificación: {calificacion}% '
            f'({correctas}/{total} correctas). '
            f'Se requiere mínimo {porcentaje_req}% para aprobar. '
            f'Puede intentar nuevamente.',
            'warning'
        )

    return render_template('empleado/resultado.html',
                           capacitacion=cap,
                           calificacion=calificacion,
                           estado=estado,
                           correctas=correctas,
                           total=total,
                           preguntas=preguntas,
                           respuestas_dadas=respuestas_dadas,
                           empleado=empleado)


# ──────────────────────────────────────────────
#  MI HISTORIAL DE CAPACITACIONES
# ──────────────────────────────────────────────
@empleado_bp.route('/mi-progreso')
@login_required
def mi_progreso():
    if current_user.role != 'Empleado':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    empleado = get_empleado()
    if not empleado:
        flash('Perfil de empleado no encontrado.', 'danger')
        return redirect(url_for('main.dashboard'))

    progresos = ProgresoCapacitacion.query.filter_by(
        empleado_id=empleado.id
    ).order_by(ProgresoCapacitacion.fecha_completado.desc()).all()

    total = len(progresos)
    aprobados = sum(1 for p in progresos if p.estado == 'Aprobado')
    pendientes = total - aprobados

    return render_template('empleado/mi_progreso.html',
                           progresos=progresos,
                           total=total,
                           aprobados=aprobados,
                           pendientes=pendientes,
                           empleado=empleado)


# ──────────────────────────────────────────────
#  VISTA PREVIA DE MATERIAL (solo visualización, sin descarga)
# ──────────────────────────────────────────────
@empleado_bp.route('/material/<int:material_id>/preview')
@login_required
def preview_material(material_id):
    """Vista previa de material para empleados (sin opción de descarga)"""
    if current_user.role != 'Empleado':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    material = MaterialCapacitacion.query.get_or_404(material_id)
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Servir archivo inline (el navegador lo muestra, no lo descarga)
    return send_from_directory(
        upload_folder,
        material.archivo_path,
        as_attachment=False  # False = vista previa, no descarga
    )
