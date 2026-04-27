# -*- coding: utf-8 -*-
"""
Rutas del Módulo de Documentación
- Repositorio centralizado para consulta de archivos según permisos
- Subir, descargar y listar documentos
- Visibilidad: Público (todos) o Privado (Admin, Gestor, RRHH)
"""

import os
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, send_from_directory, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Documento, Area

documentos_bp = Blueprint('documentos', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                      'txt', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ──────────────────────────────────────────────
#  LISTAR DOCUMENTOS
# ──────────────────────────────────────────────
@documentos_bp.route('/documentos')
@login_required
def listar():
    area_id = request.args.get('area_id', type=int)
    buscar = request.args.get('buscar', '').strip()
    vis_filtro = request.args.get('visibilidad', '').strip()

    query = Documento.query

    # Filtrar por visibilidad según rol
    # Empleados solo ven documentos públicos
    if current_user.role == 'Empleado':
        query = query.filter_by(visibilidad='publico')

    # Filtro por visibilidad seleccionado (solo para roles que pueden ver privados)
    if vis_filtro and current_user.role in ('Admin', 'Gestor', 'RRHH'):
        query = query.filter_by(visibilidad=vis_filtro)

    if area_id:
        query = query.filter_by(area_id=area_id)
    if buscar:
        query = query.filter(Documento.titulo.ilike(f'%{buscar}%'))

    documentos = query.order_by(Documento.fecha_subida.desc()).all()
    areas = Area.query.all()

    return render_template('documentos/listar.html',
                           documentos=documentos,
                           areas=areas,
                           area_seleccionada=area_id,
                           buscar=buscar,
                           vis_filtro=vis_filtro)


# ──────────────────────────────────────────────
#  SUBIR DOCUMENTO (Admin, Gestor y RRHH)
# ──────────────────────────────────────────────
@documentos_bp.route('/documentos/subir', methods=['GET', 'POST'])
@login_required
def subir():
    if current_user.role not in ('Admin', 'Gestor', 'RRHH'):
        flash('Acceso no autorizado para subir documentos.', 'danger')
        return redirect(url_for('documentos.listar'))

    areas = Area.query.all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        area_id = request.form.get('area_id', type=int)
        descripcion = request.form.get('descripcion', '').strip()
        visibilidad = request.form.get('visibilidad', 'publico').strip()
        archivo = request.files.get('archivo')

        if not titulo or not area_id:
            flash('El título y el área son obligatorios.', 'warning')
            return render_template('documentos/subir.html', areas=areas)

        if not archivo or archivo.filename == '':
            flash('Debe seleccionar un archivo.', 'warning')
            return render_template('documentos/subir.html', areas=areas)

        # Validación: gestor solo puede subir a su área
        if current_user.role == 'Gestor':
            from models import Gestor
            gestor = Gestor.query.filter_by(user_id=current_user.id).first()
            if gestor and gestor.area_id != area_id:
                flash('Solo puede subir documentos a su propia área.', 'danger')
                return render_template('documentos/subir.html', areas=areas)

        if not allowed_file(archivo.filename):
            flash('Tipo de archivo no permitido.', 'danger')
            return render_template('documentos/subir.html', areas=areas)

        filename = secure_filename(archivo.filename)
        # Agregar timestamp para evitar colisiones
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        filename = f'{timestamp}_{filename}'

        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        archivo.save(os.path.join(upload_folder, filename))

        doc = Documento(
            titulo=titulo,
            archivo_path=filename,
            area_id=area_id,
            subido_por=current_user.id,
            descripcion=descripcion,
            visibilidad=visibilidad
        )
        db.session.add(doc)
        db.session.commit()

        flash(f'Documento "{titulo}" subido correctamente.', 'success')
        return redirect(url_for('documentos.listar'))

    return render_template('documentos/subir.html', areas=areas)


# ──────────────────────────────────────────────
#  PREVISUALIZAR DOCUMENTO (todos pueden ver)
# ──────────────────────────────────────────────
@documentos_bp.route('/documentos/<int:doc_id>/preview')
@login_required
def previsualizar(doc_id):
    doc = Documento.query.get_or_404(doc_id)

    # Empleados no pueden ver documentos privados
    if current_user.role == 'Empleado' and doc.visibilidad == 'privado':
        flash('No tiene permiso para ver este documento.', 'danger')
        return redirect(url_for('documentos.listar'))

    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, doc.archivo_path,
                               as_attachment=False)


# ──────────────────────────────────────────────
#  DESCARGAR DOCUMENTO (solo Admin, Gestor, RRHH)
# ──────────────────────────────────────────────
@documentos_bp.route('/documentos/<int:doc_id>/descargar')
@login_required
def descargar(doc_id):
    doc = Documento.query.get_or_404(doc_id)

    # Empleados NO pueden descargar documentos
    if current_user.role == 'Empleado':
        flash('Los empleados no tienen permiso para descargar documentos.', 'danger')
        return redirect(url_for('documentos.listar'))

    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, doc.archivo_path,
                               as_attachment=True)


# ──────────────────────────────────────────────
#  CAMBIAR VISIBILIDAD (Admin y RRHH)
# ──────────────────────────────────────────────
@documentos_bp.route('/documentos/<int:doc_id>/visibilidad', methods=['POST'])
@login_required
def cambiar_visibilidad(doc_id):
    if current_user.role not in ('Admin', 'RRHH'):
        flash('No tiene permiso para cambiar la visibilidad.', 'danger')
        return redirect(url_for('documentos.listar'))

    doc = Documento.query.get_or_404(doc_id)
    nueva_vis = 'privado' if doc.visibilidad == 'publico' else 'publico'
    doc.visibilidad = nueva_vis
    db.session.commit()

    flash(f'Visibilidad del documento "{doc.titulo}" cambiada a {nueva_vis}.', 'success')
    return redirect(url_for('documentos.listar'))


# ──────────────────────────────────────────────
#  ELIMINAR DOCUMENTO (solo Admin)
# ──────────────────────────────────────────────
@documentos_bp.route('/documentos/<int:doc_id>/eliminar', methods=['POST'])
@login_required
def eliminar(doc_id):
    if current_user.role != 'Admin':
        flash('Solo el administrador puede eliminar documentos.', 'danger')
        return redirect(url_for('documentos.listar'))

    doc = Documento.query.get_or_404(doc_id)

    # Eliminar archivo físico
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, doc.archivo_path)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(doc)
    db.session.commit()
    flash('Documento eliminado correctamente.', 'info')
    return redirect(url_for('documentos.listar'))