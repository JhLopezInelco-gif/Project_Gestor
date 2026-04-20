# -*- coding: utf-8 -*-
"""
Script de Población Inicial de la Base de Datos
------------------------------------------------
Crea las áreas, usuarios de ejemplo y datos de prueba.
Ejecutar: python seed.py
"""

from datetime import date, datetime
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User, Area, Gestor, Empleado, Capacitacion, Pregunta

app = create_app()


def seed_areas():
    """Crear áreas de la empresa"""
    areas = [
        'Tecnología',
        'Recursos Humanos',
        'Finanzas',
        'Marketing',
        'Operaciones',
        'Ventas',
        'Legal',
        'Calidad',
    ]
    for nombre in areas:
        existe = Area.query.filter_by(nombre_area=nombre).first()
        if not existe:
            area = Area(nombre_area=nombre)
            db.session.add(area)
    db.session.commit()
    print(f'[OK] {len(areas)} areas creadas.')


def seed_admin():
    """Crear usuario Administrador"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            nombres='Administrador',
            apellidos='Sistema',
            role='Admin',
            activo=True
        )
        db.session.add(admin)
        db.session.commit()
        print('[OK] Usuario admin creado (admin / admin123)')
    else:
        print('[INFO] Usuario admin ya existe.')


def seed_gestores():
    """Crear usuarios Gestor de ejemplo"""
    gestores_data = [
        {
            'username': 'gestor.ti',
            'password': 'gestor123',
            'nombres': 'Carlos',
            'apellidos': 'Ramírez',
            'area': 'Tecnología',
            'cargo': 'Líder Técnico'
        },
        {
            'username': 'gestor.hr',
            'password': 'gestor123',
            'nombres': 'María',
            'apellidos': 'González',
            'area': 'Recursos Humanos',
            'cargo': 'Coordinadora RRHH'
        },
        {
            'username': 'gestor.fin',
            'password': 'gestor123',
            'nombres': 'Andrés',
            'apellidos': 'López',
            'area': 'Finanzas',
            'cargo': 'Director Financiero'
        },
        {
            'username': 'gestor.mkt',
            'password': 'gestor123',
            'nombres': 'Laura',
            'apellidos': 'Martínez',
            'area': 'Marketing',
            'cargo': 'Gerente de Marketing'
        },
    ]

    for data in gestores_data:
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            user = User(
                username=data['username'],
                password_hash=generate_password_hash(data['password']),
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                role='Gestor',
                activo=True
            )
            db.session.add(user)
            db.session.flush()

            area = Area.query.filter_by(nombre_area=data['area']).first()
            if area:
                gestor = Gestor(
                    user_id=user.id,
                    area_id=area.id,
                    cargo=data['cargo']
                )
                db.session.add(gestor)
                print(f'  [OK] Gestor {data["nombres"]} {data["apellidos"]} '
                      f'-> {data["area"]}')
        else:
            print(f'  [INFO] Gestor {data["username"]} ya existe.')

    db.session.commit()


def seed_empleados():
    """Crear usuarios Empleado de ejemplo"""
    empleados_data = [
        {'username': 'emp1', 'nombres': 'Juan', 'apellidos': 'Pérez',
         'cargo': 'Desarrollador Junior', 'fecha': date(2023, 3, 15)},
        {'username': 'emp2', 'nombres': 'Ana', 'apellidos': 'Torres',
         'cargo': 'Analista de RRHH', 'fecha': date(2022, 7, 1)},
        {'username': 'emp3', 'nombres': 'Pedro', 'apellidos': 'Díaz',
         'cargo': 'Contador', 'fecha': date(2021, 1, 10)},
        {'username': 'emp4', 'nombres': 'Sofía', 'apellidos': 'Vargas',
         'cargo': 'Diseñadora UX', 'fecha': date(2023, 9, 20)},
        {'username': 'emp5', 'nombres': 'Diego', 'apellidos': 'Morales',
         'cargo': 'Soporte Técnico', 'fecha': date(2024, 2, 5)},
        {'username': 'emp6', 'nombres': 'Camila', 'apellidos': 'Rojas',
         'cargo': 'Community Manager', 'fecha': date(2023, 11, 12)},
    ]

    for data in empleados_data:
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            user = User(
                username=data['username'],
                password_hash=generate_password_hash('empleado123'),
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                role='Empleado',
                activo=True
            )
            db.session.add(user)
            db.session.flush()

            empleado = Empleado(
                user_id=user.id,
                cargo=data['cargo'],
                fecha_ingreso=data['fecha']
            )
            db.session.add(empleado)
            print(f'  [OK] Empleado {data["nombres"]} {data["apellidos"]}')
        else:
            print(f'  [INFO] Empleado {data["username"]} ya existe.')

    db.session.commit()


def seed_rrhh():
    """Crear usuario RRHH de ejemplo"""
    user = User.query.filter_by(username='rrhh').first()
    if not user:
        user = User(
            username='rrhh',
            password_hash=generate_password_hash('rrhh123'),
            nombres='Patricia',
            apellidos='Hernández',
            role='RRHH',
            activo=True
        )
        db.session.add(user)
        db.session.commit()
        print('[OK] Usuario RRHH creado (rrhh / rrhh123)')
    else:
        print('[INFO] Usuario RRHH ya existe.')


def seed_capacitaciones():
    """Crear capacitaciones de ejemplo con preguntas"""
    caps_data = [
        {
            'titulo': 'Introducción a Python',
            'descripcion': 'Fundamentos del lenguaje Python para desarrollo backend.',
            'area': 'Tecnología',
            'gestor_user': 'gestor.ti',
            'material_link': 'https://www.youtube.com/watch?v=example-python',
            'preguntas': [
                {
                    'enunciado': '¿Cuál es la salida de print(type(42)) en Python?',
                    'a': "<class 'str'>",
                    'b': "<class 'int'>",
                    'c': "<class 'float'>",
                    'd': "<class 'bool'>",
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Qué palabra clave se usa para definir una función?',
                    'a': 'function',
                    'b': 'func',
                    'c': 'def',
                    'd': 'define',
                    'correcta': 'C'
                },
                {
                    'enunciado': '¿Cuál operador se usa para exponenciación?',
                    'a': '^',
                    'b': '**',
                    'c': 'exp',
                    'd': '%%',
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Qué método se usa para agregar un elemento al final de una lista?',
                    'a': 'add()',
                    'b': 'insert()',
                    'c': 'append()',
                    'd': 'push()',
                    'correcta': 'C'
                },
                {
                    'enunciado': '¿Cuál es el resultado de len([1, 2, 3, 4, 5])?',
                    'a': '4',
                    'b': '5',
                    'c': '6',
                    'd': 'Error',
                    'correcta': 'B'
                },
            ]
        },
        {
            'titulo': 'Seguridad en el Trabajo',
            'descripcion': 'Normativas básicas de seguridad laboral y prevención de riesgos.',
            'area': 'Recursos Humanos',
            'gestor_user': 'gestor.hr',
            'material_link': 'https://www.youtube.com/watch?v=example-seguridad',
            'preguntas': [
                {
                    'enunciado': '¿Qué se debe hacer primero en caso de incendio?',
                    'a': 'Correr hacia la salida',
                    'b': 'Activar la alarma de incendio',
                    'c': 'Llamar a un compañero',
                    'd': 'Intentar apagar el fuego',
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Cada cuánto se debe revisar el extintor?',
                    'a': 'Cada 5 años',
                    'b': 'Cada 6 meses',
                    'c': 'Anualmente',
                    'd': 'No es necesario revisarlo',
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Qué elemento de EPP protege la cabeza?',
                    'a': 'Guantes',
                    'b': 'Casco',
                    'c': 'Botas',
                    'd': 'Gafas',
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Qué color tienen las señales de evacuación?',
                    'a': 'Rojo',
                    'b': 'Amarillo',
                    'c': 'Verde',
                    'd': 'Azul',
                    'correcta': 'C'
                },
                {
                    'enunciado': '¿Quién es responsable de la seguridad en el trabajo?',
                    'a': 'Solo el jefe',
                    'b': 'Solo el encargado de seguridad',
                    'c': 'Todos los trabajadores',
                    'd': 'Solo los empleados nuevos',
                    'correcta': 'C'
                },
            ]
        },
        {
            'titulo': 'Gestión Financiera Básica',
            'descripcion': 'Principios de contabilidad y gestión financiera empresarial.',
            'area': 'Finanzas',
            'gestor_user': 'gestor.fin',
            'material_link': 'https://www.youtube.com/watch?v=example-finanzas',
            'preguntas': [
                {
                    'enunciado': '¿Qué es el activo en un balance general?',
                    'a': 'Lo que la empresa debe',
                    'b': 'Lo que la empresa posee',
                    'c': 'Las ganancias',
                    'd': 'Los impuestos',
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Qué estado financiero muestra los ingresos y gastos?',
                    'a': 'Balance general',
                    'b': 'Estado de resultados',
                    'c': 'Flujo de caja',
                    'd': 'Estado de patrimonio',
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Qué es la depreciación?',
                    'a': 'Un aumento del valor',
                    'b': 'Una deuda a largo plazo',
                    'c': 'La pérdida de valor de un activo',
                    'd': 'Un tipo de impuesto',
                    'correcta': 'C'
                },
                {
                    'enunciado': '¿Qué ratio mide la liquidez inmediata?',
                    'a': 'Ratio de endeudamiento',
                    'b': 'Prueba ácida',
                    'c': 'ROE',
                    'd': 'Margen neto',
                    'correcta': 'B'
                },
                {
                    'enunciado': '¿Qué significa ROI?',
                    'a': 'Return Over Investment',
                    'b': 'Return On Investment',
                    'c': 'Rate Of Interest',
                    'd': 'Revenue Of Income',
                    'correcta': 'B'
                },
            ]
        },
    ]

    for cap_data in caps_data:
        existe = Capacitacion.query.filter_by(titulo=cap_data['titulo']).first()
        if existe:
            print(f'  [INFO] Capacitacion "{cap_data["titulo"]}" ya existe.')
            continue

        area = Area.query.filter_by(nombre_area=cap_data['area']).first()
        gestor_user = User.query.filter_by(username=cap_data['gestor_user']).first()
        gestor = Gestor.query.filter_by(user_id=gestor_user.id).first() if gestor_user else None

        if not area or not gestor:
            print(f'  [WARN] No se pudo crear "{cap_data["titulo"]}" (area o gestor faltante).')
            continue

        cap = Capacitacion(
            titulo=cap_data['titulo'],
            descripcion=cap_data['descripcion'],
            area_id=area.id,
            gestor_id=gestor.id,
            material_link=cap_data['material_link'],
            activa=True
        )
        db.session.add(cap)
        db.session.flush()

        for i, preg in enumerate(cap_data['preguntas']):
            pregunta = Pregunta(
                capacitacion_id=cap.id,
                enunciado=preg['enunciado'],
                opcion_a=preg['a'],
                opcion_b=preg['b'],
                opcion_c=preg['c'],
                opcion_d=preg['d'],
                respuesta_correcta=preg['correcta']
            )
            db.session.add(pregunta)

        print(f'  [OK] Capacitacion "{cap_data["titulo"]}" con '
              f'{len(cap_data["preguntas"])} preguntas.')

    db.session.commit()


def run_seed():
    """Ejecutar todas las funciones de poblamiento"""
    print('\n' + '=' * 60)
    print('  POBLACION INICIAL DE BASE DE DATOS')
    print('=' * 60 + '\n')

    print('[*] Creando areas...')
    seed_areas()

    print('\n[*] Creando administrador...')
    seed_admin()

    print('\n[*] Creando gestores...')
    seed_gestores()

    print('\n[*] Creando empleados...')
    seed_empleados()

    print('\n[*] Creando usuario RRHH...')
    seed_rrhh()

    print('\n[*] Creando capacitaciones con preguntas...')
    seed_capacitaciones()

    print('\n' + '=' * 60)
    print('  POBLACION COMPLETADA')
    print('=' * 60)
    print('\n  CREDENCIALES DE ACCESO:')
    print('  ------------------------------------')
    print('  Admin:    admin      / admin123')
    print('  Gestor:   gestor.ti  / gestor123')
    print('  Gestor:   gestor.hr  / gestor123')
    print('  Gestor:   gestor.fin / gestor123')
    print('  Gestor:   gestor.mkt / gestor123')
    print('  Empleado: emp1       / empleado123')
    print('  Empleado: emp2       / empleado123')
    print('  Empleado: emp3       / empleado123')
    print('  RRHH:     rrhh       / rrhh123')
    print('  ------------------------------------\n')


if __name__ == '__main__':
    with app.app_context():
        run_seed()