import sqlite3

DB_PATH = "stock.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS papel_entradas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    tipo_papel TEXT NOT NULL,
    gramaje TEXT NOT NULL,
    formato TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    marca TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    observaciones TEXT
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS papel_salidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    tipo_papel TEXT NOT NULL,
    gramaje TEXT NOT NULL,
    formato TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    marca TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    observaciones TEXT
);
""")

conn.commit()
conn.close()
print("Tablas papel_entradas y papel_salidas listas")
