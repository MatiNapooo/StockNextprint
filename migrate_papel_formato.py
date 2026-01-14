import sqlite3
import shutil
import os

DB_PATH = "stock.db"

def migrate():
    print("Iniciando migración de base de datos para PAPEL (Agregar Formato)...")
    
    # 1. Backup de seguridad
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, "stock_backup_formato.db")
        print("Backup creado: stock_backup_formato.db")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    try:
        # 2. Verificar si ya existe la columna (por si acaso)
        cur.execute("PRAGMA table_info(papel_inventario)")
        columns = [row["name"] for row in cur.fetchall()]
        
        if "formato" in columns:
            print("La columna 'formato' ya existe. No es necesaria la migración.")
            return

        print("Reestructurando tabla 'papel_inventario'...")
        
        # 3. Renombrar tabla actual
        cur.execute("ALTER TABLE papel_inventario RENAME TO papel_inventario_old")
        
        # 4. Crear nueva tabla con columna 'formato'
        # Constraint UNIQUE ahora es (nombre, formato)
        cur.execute("""
            CREATE TABLE papel_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                formato TEXT NOT NULL DEFAULT 'Sin Formato',
                stock_inicial INTEGER NOT NULL DEFAULT 0,
                entradas INTEGER NOT NULL DEFAULT 0,
                salidas INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                UNIQUE(nombre, formato)
            )
        """)
        
        # 5. Migrar datos existentes
        # Asumiremos 'Sin Formato' o podemos intentar deducirlo, pero mejor 'Sin Formato' para que el usuario edite.
        # Ojo: Si hay duplicados de nombre en la vieja (no debería pq era UNIQUE), esto fallaría.
        cur.execute("""
            INSERT INTO papel_inventario (id, nombre, formato, stock_inicial, entradas, salidas, total)
            SELECT id, nombre, '70x100', stock_inicial, entradas, salidas, total
            FROM papel_inventario_old
        """)
        
        # 6. Eliminar tabla vieja (o dejarla por seguridad un tiempo, pero el usuario pidió "no romper nada", mejor limpiar)
        # Vamos a dejarla caer al final si todo sale bien.
        cur.execute("DROP TABLE papel_inventario_old")
        
        conn.commit()
        print("Migración completada con éxito.")
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR durante la migración: {e}")
        print("Restaurando backup...")
        shutil.copy2("stock_backup_formato.db", DB_PATH)
        print("Base de datos restaurada.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
