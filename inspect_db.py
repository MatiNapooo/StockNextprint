import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock.db")

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- Searching for '46' or '46cm' in papel_inventario ---")
    try:
        cursor.execute("SELECT id, nombre, formato FROM papel_inventario WHERE formato LIKE '%46%' OR nombre LIKE '%46%'")
        rows = cursor.fetchall()
        if not rows:
            print("No matching rows found.")
        else:
            for row in rows:
                print(f"ID: {row[0]}, Nombre: {row[1]}, Formato: {row[2]}")
    except sqlite3.OperationalError as e:
        print(f"Error querying database: {e}")
    
    print("\n--- Distinct Formats ---")
    try:
        cursor.execute("SELECT DISTINCT formato FROM papel_inventario")
        formats = cursor.fetchall()
        for f in formats:
            print(f[0])
    except Exception as e:
        print(f"Error getting formats: {e}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
