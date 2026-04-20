# -*- coding: utf-8 -*-
"""
Rutas del Módulo Gestor
- Subir material (links o rutas de archivos)
- Crear capacitaciones y cuestionarios asociados a su área
- Validación: un gestor solo puede gestionar contenido de su propia área
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import (db, Gestor, Capacitacion, Pregunta, Area,
                    ProgresoCapacitacion)

gestor_bp = Blueprint('gestor', __name__)


def get_gestor():
    """Obtener el perfil de gestor del usuario actual"""
    return Gestor.query.filter_by(user_id=current_user.id).first()


# ──────────────────────────────────────────────
#  LISTAR CAPACITACIONES DEL GESTOR
# ──────────────────────────────────────────────
@gestor_bp.route('/mis-capacitaciones')
@login_required
def mis_capacitaciones():
    if current_user.role != 'Gestor':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    gestor = get_gestor()
    if not gestor:
        flash('Perfil de gestor no encontrado.', 'danger')
        return redirect(url_for('main.dashboard'))

    capacitaciones = Capacitacion.query.filter_by(
        gestor_id=gestor.id
    ).order_by(Capacitacion.fecha_creacion.desc()).all()

    return render_template('gestor/mis_capacitaciones.html',
                           capacitaciones=capacitaciones, gestor=gestor)


# ──────────────────────────────────────────────
#  CREAR CAPACITACIÓN
# ──────────────────────────────────────────────
@gestor_bp.route('/capacitacion/crear', methods=['GET', 'POST'])
@login_required
def crear_capacitacion():
    if current_user.role != 'Gestor':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    gestor = get_gestor()
    if not gestor:
        flash('Perfil de gestor no encontrado.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        material_link = request.form.get('material_link', '').strip()

        # Validación: el área se asigna automáticamente según el gestor
        area_id = gestor.area_id

        if not titulo:
            flash('El título es obligatorio.', 'warning')
            return render_template('gestor/crear_capacitacion.html', gestor=gestor)

        nueva = Capacitacion(
            titulo=titulo,
            descripcion=descripcion,
            area_id=area_id,
            gestor_id=gestor.id,
            material_link=material_link,
            activa=True
        )
        db.session.add(nueva)
        db.session.commit()

        flash(f'Capacitación "{titulo}" creada correctamente.', 'success')
        return redirect(url_for('gestor.agregar_preguntas',
                                capacitacion_id=nueva.id))

    return render_template('gestor/crear_capacitacion.html', gestor=gestor)


# ──────────────────────────────────────────────
#  EDITAR CAPACITACIÓN
# ──────────────────────────────────────────────
@gestor_bp.route('/capacitacion/<int:capacitacion_id>/editar',
                 methods=['GET', 'POST'])
@login_required
def editar_capacitacion(capacitacion_id):
    gestor = get_gestor()
    if not gestor:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    cap = Capacitacion.query.get_or_404(capacitacion_id)

    # Validación: solo puede editar capacitaciones de su área
    if cap.gestor_id != gestor.id:
        flash('No tiene permisos para editar esta capacitación.', 'danger')
        return redirect(url_for('gestor.mis_capacitaciones'))

    if request.method == 'POST':
        cap.titulo = request.form.get('titulo', '').strip()
        cap.descripcion = request.form.get('descripcion', '').strip()
        cap.material_link = request.form.get('material_link', '').strip()
        cap.activa = 'activa' in request.form

        db.session.commit()
        flash('Capacitación actualizada correctamente.', 'success')
        return redirect(url_for('gestor.mis_capacitaciones'))

    return render_template('gestor/editar_capacitacion.html',
                           capacitacion=cap, gestor=gestor)


# ──────────────────────────────────────────────
#  AGREGAR PREGUNTAS A CUESTIONARIO
# ──────────────────────────────────────────────
@gestor_bp.route('/capacitacion/<int:capacitacion_id>/preguntas',
                 methods=['GET', 'POST'])
@login_required
def agregar_preguntas(capacitacion_id):
    gestor = get_gestor()
    if not gestor:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    cap = Capacitacion.query.get_or_404(capacitacion_id)

    # Validación: solo el gestor creador puede agregar preguntas
    if cap.gestor_id != gestor.id:
        flash('No tiene permisos para esta capacitación.', 'danger')
        return redirect(url_for('gestor.mis_capacitaciones'))

    if request.method == 'POST':
        enunciado = request.form.get('enunciado', '').strip()
        opcion_a = request.form.get('opcion_a', '').strip()
        opcion_b = request.form.get('opcion_b', '').strip()
        opcion_c = request.form.get('opcion_c', '').strip()
        opcion_d = request.form.get('opcion_d', '').strip()
        respuesta_correcta = request.form.get('respuesta_correcta', 'A').upper()

        if not all([enunciado, opcion_a, opcion_b, opcion_c, opcion_d]):
            flash('Todos los campos de la pregunta son obligatorios.', 'warning')
        else:
            pregunta = Pregunta(
                capacitacion_id=cap.id,
                enunciado=enunciado,
                opcion_a=opcion_a,
                opcion_b=opcion_b,
                opcion_c=opcion_c,
                opcion_d=opcion_d,
                respuesta_correcta=respuesta_correcta
            )
            db.session.add(pregunta)
            db.session.commit()
            flash('Pregunta agregada correctamente.', 'success')

    preguntas = Pregunta.query.filter_by(capacitacion_id=cap.id).all()
    return render_template('gestor/preguntas.html',
                           capacitacion=cap, preguntas=preguntas, gestor=gestor)


# ──────────────────────────────────────────────
#  ELIMINAR PREGUNTA
# ──────────────────────────────────────────────
@gestor_bp.route('/pregunta/<int:pregunta_id>/eliminar', methods=['POST'])
@login_required
def eliminar_pregunta(pregunta_id):
    gestor = get_gestor()
    if not gestor:
        return jsonify({'error': 'No autorizado'}), 403

    pregunta = Pregunta.query.get_or_404(pregunta_id)
    cap = Capacitacion.query.get(pregunta.capacitacion_id)

    if cap.gestor_id != gestor.id:
        return jsonify({'error': 'No autorizado'}), 403

    capacitacion_id = pregunta.capacitacion_id
    db.session.delete(pregunta)
    db.session.commit()
    flash('Pregunta eliminada.', 'info')
    return redirect(url_for('gestor.agregar_preguntas',
                            capacitacion_id=capacitacion_id))


# ──────────────────────────────────────────────
#  VER RESULTADOS DE MI CAPACITACIÓN
# ──────────────────────────────────────────────
@gestor_bp.route('/capacitacion/<int:capacitacion_id>/resultados')
@login_required
def ver_resultados(capacitacion_id):
    gestor = get_gestor()
    if not gestor:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    cap = Capacitacion.query.get_or_404(capacitacion_id)
    if cap.gestor_id != gestor.id:
        flash('No tiene permisos para ver estos resultados.', 'danger')
        return redirect(url_for('gestor.mis_capacitaciones'))

    progresos = ProgresoCapacitacion.query.filter_by(
        capacitacion_id=cap.id
    ).all()

    return render_template('gestor/resultados.html',
                           capacitacion=cap, progresos=progresos, gestor=gestor)