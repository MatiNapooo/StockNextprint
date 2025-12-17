import sqlite3

DB_PATH = "stock.db"   # mismo nombre que usás en get_db_connection()

papeles = [
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
    # el último "Quimico CF Verde" estaba repetido, lo dejamos una sola vez
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Crear tabla de inventario de papel
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

# Insertar tipos de papel (si ya existen, no los duplica)
for nombre in papeles:
    cur.execute(
        "INSERT OR IGNORE INTO papel_inventario (nombre) VALUES (?)",
        (nombre,)
    )

conn.commit()
conn.close()
print("Tabla papel_inventario creada/cargada.")
