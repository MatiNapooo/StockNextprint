import sqlite3

DB_PATH = "stock.db"   # mismo nombre que usás en get_db_connection()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Agrega la columna solo si no existe
try:
    cur.execute("ALTER TABLE pedidos ADD COLUMN insumo_codigo TEXT")
    print("Columna insumo_codigo agregada a pedidos.")
except sqlite3.OperationalError:
    print("La columna insumo_codigo ya existe. No se hizo nada.")

conn.commit()
conn.close()
