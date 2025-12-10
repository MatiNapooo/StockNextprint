import sqlite3

conn = sqlite3.connect("stock.db")
cursor = conn.cursor()

# insumos (ya existía)
cursor.execute("""
CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    unidad TEXT
)
""")

# entradas (ya la teníamos)
cursor.execute("""
CREATE TABLE IF NOT EXISTS entradas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    insumo_codigo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    FOREIGN KEY (insumo_codigo) REFERENCES insumos(codigo)
)
""")

# salidas (ya la teníamos)
cursor.execute("""
CREATE TABLE IF NOT EXISTS salidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    insumo_codigo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    FOREIGN KEY (insumo_codigo) REFERENCES insumos(codigo)
)
""")

# NUEVO: inventario
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insumo_codigo TEXT NOT NULL UNIQUE,
    stock_inicial INTEGER NOT NULL DEFAULT 0,
    entradas INTEGER NOT NULL DEFAULT 0,
    salidas INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (insumo_codigo) REFERENCES insumos(codigo)
)
""")

# Asegurar que todos los insumos tengan fila en inventario
cursor.execute("""
INSERT OR IGNORE INTO inventario (insumo_codigo, stock_inicial, entradas, salidas, total)
SELECT codigo, 0, 0, 0, 0
FROM insumos
""")

conn.commit()
conn.close()

print("Base de datos lista: insumos, entradas, salidas, inventario.")
