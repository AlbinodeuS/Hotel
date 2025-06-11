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

# --- DATOS DE EJEMPLO ---
# Usuarios
admin_password = generate_password_hash('admin')
cur.execute("INSERT INTO usuarios (username, password_hash, role) VALUES (?, ?, ?)", ('admin', admin_password, 'kroot'))
cur.execute("INSERT INTO usuarios (username, password_hash, role) VALUES (?, ?, ?)", ('staff', generate_password_hash('1234'), 'staff'))

# Edificios
cur.execute("INSERT INTO edificios (nombre, direccion) VALUES (?, ?)", ('Torre Principal', 'Av. Principal 123'))
cur.execute("INSERT INTO edificios (nombre, direccion) VALUES (?, ?)", ('Anexo Playa', 'Calle Costa 456'))

# Personal
cur.execute("INSERT INTO personal (id_edificio, nombre_completo, puesto) VALUES (?, ?, ?)", (1, 'Juan Pérez', 'Recepcionista Principal'))
cur.execute("INSERT INTO personal (id_edificio, nombre_completo, puesto) VALUES (?, ?, ?)", (2, 'Carlos Ruiz', 'Recepcionista Anexo'))

# Habitaciones
cur.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo) VALUES (?, ?, ?)", (1, '101', 'Individual'))
cur.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo, estado) VALUES (?, ?, ?, ?)", (1, '102', 'Doble', 'Ocupada'))
cur.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo) VALUES (?, ?, ?)", (2, 'A01', 'Suite'))

# Clientes
cur.execute("INSERT INTO clientes (nombre_completo, rut_documento, email) VALUES (?, ?, ?)", ('Ana Martínez', '11.111.111-1', 'ana.martinez@email.com'))
cur.execute("INSERT INTO clientes (nombre_completo, rut_documento, email) VALUES (?, ?, ?)", ('Luis García', '22.222.222-2', 'luis.garcia@email.com'))

# Reservas
cur.execute("UPDATE habitaciones SET estado = 'Ocupada', fecha_disponible = '2025-06-15' WHERE id = 2")
cur.execute("INSERT INTO reservas (id_cliente, id_habitacion, fecha_check_in, fecha_check_out) VALUES (?, ?, ?, ?)", (1, 2, '2025-06-10', '2025-06-15'))

# Servicios Adicionales
cur.execute("INSERT INTO servicios_adicionales (nombre_servicio, precio) VALUES (?, ?)", ('Desayuno Buffet', 15000))
cur.execute("INSERT INTO servicios_adicionales (nombre_servicio, precio) VALUES (?, ?)", ('Acceso a Spa', 30000))

connection.commit()
connection.close()

print(f"Base de datos '{DB_FILE}' creada con toda la estructura y datos de ejemplo.")
print("Usuario Admin: admin / Pass: admin")
print("Usuario Staff: staff / Pass: 1234")
