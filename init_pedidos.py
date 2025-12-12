import sqlite3

# Asegurate de que este nombre sea el mismo que usás en get_db_connection()
DB_PATH = "stock.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    pedido_por TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    insumo TEXT NOT NULL,
    presentacion TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    estado TEXT NOT NULL DEFAULT 'En Espera'
);
""")

conn.commit()
conn.close()
print("Tabla 'pedidos' creada (o ya existía).")
