import sqlite3

# OJO: si tu archivo de base de datos NO se llama stock.db, cambia el nombre aquí
DB_NAME = "stock.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS papel_pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    tipo_papel TEXT NOT NULL,
    gramaje TEXT NOT NULL,
    formato TEXT NOT NULL,
    marca TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'En espera'
);
""")

conn.commit()
conn.close()
print("Tabla papel_pedidos creada / ya existía.")
