DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS habitaciones;
DROP TABLE IF EXISTS personal;
DROP TABLE IF EXISTS edificios;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS reservas;
DROP TABLE IF EXISTS servicios_adicionales;

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff' -- 'kroot' para admin, 'staff' para otros
);

CREATE TABLE edificios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    direccion TEXT NOT NULL
);

CREATE TABLE personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_edificio INTEGER NOT NULL, -- Personal pertenece a un edificio
    nombre_completo TEXT NOT NULL,
    puesto TEXT NOT NULL,
    telefono TEXT,
    FOREIGN KEY (id_edificio) REFERENCES edificios (id)
);

CREATE TABLE habitaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_edificio INTEGER NOT NULL,
    numero_habitacion TEXT NOT NULL,
    tipo TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Disponible',
    fecha_disponible TEXT, -- Para saber hasta cuándo está ocupada/mantenimiento
    id_personal_asignado INTEGER,
    FOREIGN KEY (id_edificio) REFERENCES edificios (id),
    FOREIGN KEY (id_personal_asignado) REFERENCES personal (id)
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    rut_documento TEXT UNIQUE NOT NULL,
    email TEXT,
    telefono TEXT
);

CREATE TABLE reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL,
    id_habitacion INTEGER NOT NULL,
    fecha_check_in TEXT NOT NULL,
    fecha_check_out TEXT NOT NULL,
    FOREIGN KEY (id_cliente) REFERENCES clientes (id),
    FOREIGN KEY (id_habitacion) REFERENCES habitaciones (id)
);

CREATE TABLE servicios_adicionales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_servicio TEXT NOT NULL,
    precio REAL NOT NULL
);
