import sqlite3
import os

# Buscamos la base de datos en la misma carpeta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "stock.db")

def arreglar_base_datos():
    print(f"Conectando a la base de datos en: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        # Comando SQL para agregar la columna que falta
        conn.execute("ALTER TABLE papel_pedidos ADD COLUMN pedido_por TEXT")
        conn.commit()
        print("✅ ¡ÉXITO! Se agregó la columna 'pedido_por' correctamente.")
    except sqlite3.OperationalError as e:
        # Si dice que ya existe, es que ya se arregló antes
        if "duplicate column name" in str(e):
            print("ℹ️ La columna 'pedido_por' ya existe. No hace falta hacer nada.")
        else:
            print(f"❌ Ocurrió un error: {e}")
    finally:
        conn.close()
        print("Cerrando conexión.")

if __name__ == "__main__":
    arreglar_base_datos()