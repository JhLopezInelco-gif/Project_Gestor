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
    material_link = db.Column(db.String(500), default='')  # Video/PDF link
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Preguntas del cuestionario
    preguntas = db.relationship('Pregunta', backref='capacitacion', lazy=True,
                                cascade='all, delete-orphan')
    # Progreso de empleados
    progreso = db.relationship('ProgresoCapacitacion', backref='capacitacion', lazy=True)

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
    def determinar_estado(calificacion):
        """Aprobado solo si calificación >= 80%"""
        return 'Aprobado' if calificacion >= 80 else 'Pendiente'