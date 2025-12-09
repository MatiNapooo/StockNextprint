import sqlite3

# 1) Conectarse (si el archivo no existe, lo crea)
conn = sqlite3.connect("stock.db")
cursor = conn.cursor()

# 2) Crear la tabla de insumos (solo la primera vez)
cursor.execute("""
CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    unidad TEXT
)
""")

# 3) Confirmar cambios y cerrar
conn.commit()
conn.close()

print("Base de datos creada y tabla 'insumos' lista.")
