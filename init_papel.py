import sqlite3

DB_PATH = "stock.db"

# Lista completa provista
raw_papeles = [
    "Obra",
    "Ilustración Mate",
    "Ilustración Brillo",
    "Comercial Verde",
    "Comercial Amarillo",
    "Comercial Celeste",
    "Comercial Rosa",
    "Bookcel",
    "Cartulina Duplex",
    "Cartulina Triplex",
    "Autoadhesivo Obra",
    "Autoadhesivo Obra con medio corte",
    "Autoadhesivo Ilustración",
    "Autoadhesivo Ilustración con medio corte",
    "Quimico CF Blanco",
    "Quimico CF Amarillo",
    "Quimico CF Rosa",
    "Quimico CF Celeste",
    "Quimico CF Verde",
    "Quimico CFB Blanco",
    "Quimico CFB Amarillo",
    "Quimico CFB Rosa",
    "Quimico CFB Celeste",
    "Quimico CFB Verde",
    "Quimico CB Blanco",
    "Quimico CB Amarillo",
    "Quimico CB Rosa",
    "Quimico CB Celeste",
    "Quimico CF Verde"
]

# Eliminamos duplicados y ordenamos alfabéticamente
papeles = sorted(list(set(raw_papeles)))

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Crear tabla de inventario de papel si no existe
cur.execute("""
CREATE TABLE IF NOT EXISTS papel_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    stock_inicial INTEGER NOT NULL DEFAULT 0,
    entradas INTEGER NOT NULL DEFAULT 0,
    salidas INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0
);
""")

# Insertar tipos de papel (IGNORE para no duplicar si ya existen)
for nombre in papeles:
    cur.execute(
        "INSERT OR IGNORE INTO papel_inventario (nombre) VALUES (?)",
        (nombre,)
    )

conn.commit()
conn.close()
print(f"Base de datos de papel actualizada con {len(papeles)} tipos ordenados.")