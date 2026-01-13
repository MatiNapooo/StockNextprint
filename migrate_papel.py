import sqlite3
import os
import sys

def migrate_db():
    # Force CWD to script directory just in case
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    db_path = "stock.db"
    
    # Check if we are in Railway (optional check, but good for local dev consistency)
    railway_volumen = "/app/datos"
    if os.path.exists(railway_volumen):
        db_path = os.path.join(railway_volumen, "stock.db")
        
    print(f"Connecting to database at: {db_path}")
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    try:
        # 1. Add 'afecta_stock' column to 'papel_pedidos'
        print("Adding column 'afecta_stock' to table 'papel_pedidos'...")
        conn.execute("ALTER TABLE papel_pedidos ADD COLUMN afecta_stock INTEGER DEFAULT 1")
        print("Column 'afecta_stock' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'afecta_stock' already exists.")
        else:
            print(f"Error adding column: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_db()
