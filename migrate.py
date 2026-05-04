# -*- coding: utf-8 -*-
"""
Script de migración para agregar:
- Tabla material_capacitacion
- Columna porcentaje_aprobacion en capacitacion
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'gestor.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Agregar columna porcentaje_aprobacion a capacitacion si no existe
    try:
        cursor.execute("""
            ALTER TABLE capacitacion 
            ADD COLUMN porcentaje_aprobacion INTEGER DEFAULT 80
        """)
        print("[OK] Columna 'porcentaje_aprobacion' agregada a tabla 'capacitacion'")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print("[=] Columna 'porcentaje_aprobacion' ya existe en 'capacitacion'")
        else:
            print(f"[!] Error: {e}")

    # 2. Crear tabla material_capacitacion si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_capacitacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capacitacion_id INTEGER NOT NULL,
            tipo VARCHAR(20) DEFAULT 'archivo',
            titulo VARCHAR(200) DEFAULT '',
            url VARCHAR(500) DEFAULT '',
            archivo_path VARCHAR(500) DEFAULT '',
            nombre_original VARCHAR(300) DEFAULT '',
            tipo_mime VARCHAR(100) DEFAULT '',
            tamaño INTEGER DEFAULT 0,
            fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (capacitacion_id) REFERENCES capacitacion(id)
        )
    """)
    print("[OK] Tabla 'material_capacitacion' creada/verificada")

    conn.commit()
    conn.close()
    print("\nMigración completada exitosamente.")

if __name__ == '__main__':
    migrate()