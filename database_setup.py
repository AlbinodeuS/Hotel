import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_FILE = 'hotel.db'
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

connection = sqlite3.connect(DB_FILE)
with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

# --- Crear Usuario Admin ---
# Contraseña es "admin". Se guarda hasheada por seguridad.
admin_password = generate_password_hash('admin')
cur.execute("INSERT INTO usuarios (username, password_hash, role) VALUES (?, ?, ?)",
            ('admin', admin_password, 'kroot'))

# --- Crear Edificios ---
cur.execute("INSERT INTO edificios (nombre, direccion) VALUES (?, ?)", ('Torre Principal', 'Av. Principal 123'))
cur.execute("INSERT INTO edificios (nombre, direccion) VALUES (?, ?)", ('Anexo Playa', 'Calle Costa 456'))

# --- Crear Personal y asignarlo a edificios ---
cur.execute("INSERT INTO personal (id_edificio, nombre_completo, puesto) VALUES (?, ?, ?)", (1, 'Juan Pérez', 'Recepcionista Principal'))
cur.execute("INSERT INTO personal (id_edificio, nombre_completo, puesto) VALUES (?, ?, ?)", (1, 'Ana Gómez', 'Limpieza Torre'))
cur.execute("INSERT INTO personal (id_edificio, nombre_completo, puesto) VALUES (?, ?, ?)", (2, 'Carlos Ruiz', 'Recepcionista Anexo'))
cur.execute("INSERT INTO personal (id_edificio, nombre_completo, puesto) VALUES (?, ?, ?)", (2, 'María Soto', 'Limpieza Playa'))

# --- Crear Habitaciones y asignarlas a edificios ---
cur.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo) VALUES (?, ?, ?)", (1, '101', 'Individual'))
cur.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo) VALUES (?, ?, ?)", (1, '102', 'Doble'))
cur.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo) VALUES (?, ?, ?)", (2, 'A01', 'Suite'))
cur.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo) VALUES (?, ?, ?)", (2, 'A02', 'Individual'))

connection.commit()
connection.close()

print(f"Base de datos '{DB_FILE}' creada con éxito.")
print("Usuario por defecto: admin, Contraseña: admin")