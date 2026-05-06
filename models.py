# -*- coding: utf-8 -*-
"""
Modelos de SQLAlchemy - Base de Datos Normalizada
Relaciones:
  - User 1:1 Gestor  (un usuario puede ser gestor)
  - User 1:1 Empleado (un usuario puede ser empleado)
  - Area 1:N Documento
  - Area 1:N Capacitacion
  - Area 1:N Gestor
  - Gestor 1:N Capacitacion
  - Capacitacion 1:N Pregunta
  - Empleado 1:N Progreso_Capacitacion
  - Capacitacion 1:N Progreso_Capacitacion
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ──────────────────────────────────────────────
#  USUARIO (Tabla base con datos personales)
# ──────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombres = db.Column(db.String(120), nullable=False, default='')
    apellidos = db.Column(db.String(120), nullable=False, default='')
    role = db.Column(db.String(20), nullable=False, default='Empleado')
    # Roles: Admin, Gestor, Empleado, RRHH
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones inversas
    gestor = db.relationship('Gestor', backref='user', uselist=False, lazy=True)
    empleado = db.relationship('Empleado', backref='user', uselist=False, lazy=True)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'.strip()


# ──────────────────────────────────────────────
#  ÁREA
# ──────────────────────────────────────────────
class Area(db.Model):
    __tablename__ = 'area'

    id = db.Column(db.Integer, primary_key=True)
    nombre_area = db.Column(db.String(100), unique=True, nullable=False)

    # Relaciones inversas
    gestores = db.relationship('Gestor', backref='area', lazy=True)
    documentos = db.relationship('Documento', backref='area', lazy=True)
    capacitaciones = db.relationship('Capacitacion', backref='area', lazy=True)

    def __repr__(self):
        return f'<Area {self.nombre_area}>'


# ──────────────────────────────────────────────
#  GESTOR (Extiende User con área y cargo)
# ──────────────────────────────────────────────
class Gestor(db.Model):
    __tablename__ = 'gestor'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    cargo = db.Column(db.String(100), nullable=False, default='Gestor')

    # Relación inversa: capacitaciones creadas por este gestor
    capacitaciones = db.relationship('Capacitacion', backref='gestor', lazy=True)

    def __repr__(self):
        return f'<Gestor {self.user.nombre_completo} - {self.area.nombre_area}>'


# ──────────────────────────────────────────────
#  EMPLEADO (Extiende User con cargo y fecha)
# ──────────────────────────────────────────────
class Empleado(db.Model):
    __tablename__ = 'empleado'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cargo = db.Column(db.String(100), nullable=False, default='Empleado')
    fecha_ingreso = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    # Relación inversa: progreso de capacitaciones
    progreso_capacitaciones = db.relationship(
        'ProgresoCapacitacion', backref='empleado', lazy=True
    )

    def __repr__(self):
        return f'<Empleado {self.user.nombre_completo}>'


# ──────────────────────────────────────────────
#  DOCUMENTO (Repositorio centralizado)
# ──────────────────────────────────────────────
class Documento(db.Model):
    __tablename__ = 'documento'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    archivo_path = db.Column(db.String(500), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    subido_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    descripcion = db.Column(db.Text, default='')
    visibilidad = db.Column(db.String(20), nullable=False, default='publico')
    # visibilidad: 'publico' (todos lo ven) o 'privado' (solo Admin, Gestor, RRHH)

    user = db.relationship('User', foreign_keys=[subido_por])

    def __repr__(self):
        return f'<Documento {self.titulo}>'


# ──────────────────────────────────────────────
#  CAPACITACIÓN (Curso)
# ──────────────────────────────────────────────
class Capacitacion(db.Model):
    __tablename__ = 'capacitacion'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, default='')
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    gestor_id = db.Column(db.Integer, db.ForeignKey('gestor.id'), nullable=False)
    material_link = db.Column(db.String(500), default='')  # Video/PDF link (legacy)
    porcentaje_aprobacion = db.Column(db.Integer, default=80)  # % mínimo para aprobar
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Preguntas del cuestionario
    preguntas = db.relationship('Pregunta', backref='capacitacion', lazy=True,
                                cascade='all, delete-orphan')
    # Progreso de empleados
    progreso = db.relationship('ProgresoCapacitacion', backref='capacitacion', lazy=True)
    # Materiales adjuntos
    materiales = db.relationship('MaterialCapacitacion', backref='capacitacion', lazy=True,
                                 cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Capacitacion {self.titulo}>'


# ──────────────────────────────────────────────
#  PREGUNTA (De un cuestionario de capacitación)
# ──────────────────────────────────────────────
class Pregunta(db.Model):
    __tablename__ = 'pregunta'

    id = db.Column(db.Integer, primary_key=True)
    capacitacion_id = db.Column(
        db.Integer, db.ForeignKey('capacitacion.id'), nullable=False
    )
    enunciado = db.Column(db.Text, nullable=False)
    opcion_a = db.Column(db.String(300), nullable=False, default='')
    opcion_b = db.Column(db.String(300), nullable=False, default='')
    opcion_c = db.Column(db.String(300), nullable=False, default='')
    opcion_d = db.Column(db.String(300), nullable=False, default='')
    respuesta_correcta = db.Column(db.String(1), nullable=False, default='A')
    # Respuesta correcta: A, B, C o D

    def __repr__(self):
        return f'<Pregunta Cap{self.capacitacion_id} - {self.enunciado[:30]}>'


# ──────────────────────────────────────────────
#  PROGRESO CAPACITACIÓN
# ──────────────────────────────────────────────
class ProgresoCapacitacion(db.Model):
    __tablename__ = 'progreso_capacitacion'

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(
        db.Integer, db.ForeignKey('empleado.id'), nullable=False
    )
    capacitacion_id = db.Column(
        db.Integer, db.ForeignKey('capacitacion.id'), nullable=False
    )
    calificacion = db.Column(db.Integer, default=0)  # 0-100
    estado = db.Column(db.String(20), default='Pendiente')  # Pendiente/Aprobado
    fecha_completado = db.Column(db.DateTime, nullable=True)
    respuestas_json = db.Column(db.Text, default='')  # JSON con las respuestas dadas

    # Restricción: un empleado no puede tener duplicada la misma capacitación
    __table_args__ = (
        db.UniqueConstraint(
            'empleado_id', 'capacitacion_id',
            name='uq_empleado_capacitacion'
        ),
    )

    def __repr__(self):
        return (f'<Progreso Emp{self.empleado_id} Cap{self.capacitacion_id} '
                f'{self.estado} {self.calificacion}%>')

    @staticmethod
    def calcular_calificacion(respuestas_dadas, preguntas):
        """
        Calcula el porcentaje de aprobación.
        resultado = (respuestas_correctas / total_preguntas) * 100
        """
        if not preguntas:
            return 0
        correctas = 0
        total = len(preguntas)
        for pregunta in preguntas:
            respuesta_dada = respuestas_dadas.get(str(pregunta.id), '').upper()
            if respuesta_dada == pregunta.respuesta_correcta.upper():
                correctas += 1
        calificacion = int((correctas / total) * 100)
        return calificacion

    @staticmethod
    def determinar_estado(calificacion, porcentaje_aprobacion=80):
        """Aprobado si calificación >= porcentaje_aprobacion (configurable por gestor)"""
        return 'Aprobado' if calificacion >= porcentaje_aprobacion else 'Pendiente'


# ──────────────────────────────────────────────
#  MATERIAL DE CAPACITACIÓN (archivos adjuntos)
# ──────────────────────────────────────────────
class MaterialCapacitacion(db.Model):
    __tablename__ = 'material_capacitacion'

    id = db.Column(db.Integer, primary_key=True)
    capacitacion_id = db.Column(
        db.Integer, db.ForeignKey('capacitacion.id'), nullable=False
    )
    tipo = db.Column(db.String(20), nullable=False, default='archivo')
    # tipo: 'link', 'archivo'
    titulo = db.Column(db.String(200), nullable=False, default='')
    url = db.Column(db.String(500), default='')  # Para links
    archivo_path = db.Column(db.String(500), default='')  # Para archivos subidos
    nombre_original = db.Column(db.String(300), default='')  # Nombre original del archivo
    tipo_mime = db.Column(db.String(100), default='')  # MIME type
    tamaño = db.Column(db.Integer, default=0)  # Tamaño en bytes
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Material {self.tipo}: {self.titulo}>'

    @property
    def es_imagen(self):
        return self.tipo_mime.startswith('image/')

    @property
    def es_video(self):
        return self.tipo_mime.startswith('video/') or (
            self.tipo == 'link' and ('youtube' in self.url.lower() or 'vimeo' in self.url.lower())
        )

    @property
    def es_pdf(self):
        return self.tipo_mime == 'application/pdf'

    @property
    def es_audio(self):
        return self.tipo_mime.startswith('audio/')

    @property
    def icono_bootstrap(self):
        """Retorna el icono de Bootstrap Icons según el tipo de archivo"""
        if self.tipo == 'link':
            return 'bi-link-45deg'
        if self.es_video:
            return 'bi-play-circle'
        if self.es_imagen:
            return 'bi-image'
        if self.es_pdf:
            return 'bi-file-pdf'
        if self.es_audio:
            return 'bi-music-note'
        if 'word' in self.tipo_mime or 'document' in self.tipo_mime:
            return 'bi-file-word'
        if 'excel' in self.tipo_mime or 'spreadsheet' in self.tipo_mime:
            return 'bi-file-excel'
        if 'powerpoint' in self.tipo_mime or 'presentation' in self.tipo_mime:
            return 'bi-file-ppt'
        if 'zip' in self.tipo_mime or 'rar' in self.tipo_mime:
            return 'bi-file-zip'
        return 'bi-file-earmark'


# ──────────────────────────────────────────────
#  REPORTE FGH-22: ENTRENAMIENTO EN EL PUESTO DE TRABAJO
# ──────────────────────────────────────────────
class ReporteControl(db.Model):
    __tablename__ = 'reporte_control'

    # Metadatos estáticos del formulario
    EMPRESA = 'INELCO'
    TITULO = 'ENTRENAMIENTO EN EL PUESTO DE TRABAJO'
    CODIGO = 'FGH-22'
    VERSION = '02'
    FECHA_FORMULARIO = '24-04-2025'

    id = db.Column(db.Integer, primary_key=True)
    consecutivo = db.Column(db.Integer, nullable=False, unique=True)

    # Sección I: INFORMACIÓN BÁSICA
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    nombres_apellidos = db.Column(db.String(200), nullable=False, default='')
    fecha_ingreso = db.Column(db.Date, nullable=False)
    cargo_desempenar = db.Column(db.String(150), nullable=False, default='')
    vinculacion = db.Column(db.Boolean, default=False)
    dependencia = db.Column(db.String(150), nullable=False, default='')

    # Estado del reporte
    estado = db.Column(db.String(30), nullable=False, default='En Proceso')
    # Estados: En Proceso, Completado, Aprobado

    # Auditoría
    creado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_cierre = db.Column(db.DateTime, nullable=True)

    # Relaciones
    empleado = db.relationship('Empleado', foreign_keys=[empleado_id])
    user = db.relationship('User', foreign_keys=[creado_por])
    cronograma = db.relationship(
        'CronogramaItem', backref='reporte', lazy=True,
        cascade='all, delete-orphan',
        order_by='CronogramaItem.seccion, CronogramaItem.posicion'
    )

    def __repr__(self):
        return f'<ReporteControl {self.CODIGO}-{self.consecutivo:04d}>'

    @property
    def codigo_completo(self):
        return f'{self.CODIGO}-{self.consecutivo:04d}'

    # Temas predefinidos Sección II
    TEMAS_PREDEFINIDOS = [
        'Bienvenida al área',
        'Capacitación en el sistema de Gestión de Calidad',
        'Presentación del equipo de trabajo',
        'Entrega del puesto y herramientas de trabajo (Usuario, programas y sistemas)',
        'Socialización de funciones o actividades a desarrollar',
        'Socialización de Proceso - Subprocesos y Procedimientos en los cuales participa',
        'Entrenamiento en Seguridad y Salud en el Trabajo',
    ]


class CronogramaItem(db.Model):
    __tablename__ = 'cronograma_item'

    id = db.Column(db.Integer, primary_key=True)
    reporte_id = db.Column(
        db.Integer, db.ForeignKey('reporte_control.id'), nullable=False
    )
    seccion = db.Column(db.String(5), nullable=False, default='II')
    # Sección II (predefinidos) o Sección III (temas específicos)
    posicion = db.Column(db.Integer, nullable=False, default=0)
    tema = db.Column(db.String(300), nullable=False, default='')
    fecha_realizacion = db.Column(db.Date, nullable=True)
    entrenador_asignado = db.Column(db.String(200), default='')
    firma_entrenador = db.Column(db.String(200), default='')

    def __repr__(self):
        return f'<CronogramaItem R{self.reporte_id} S{self.seccion} {self.tema[:30]}>'
