import sqlite3

# Lista original basada en tu captura:
# (codigo, insumo, descripcion_excel)
INSUMOS_ORIGINALES = [
    ("P001", "Tintas", "Magenta x 2,5 kg"),
    ("P002", "Tintas", "Cyan x 2,5 kg"),
    ("P003", "Tintas", "Amarillo x 2,5 kg"),
    ("P004", "Tintas", "Negro x 2,5 kg"),
    ("P005", "Alcohol", "Isopropilico x 18 Litros"),
    ("P006", "Desengrasante", "Preklin x 18 Litros"),
    ("P007", "Goma", "Goma Arabiga x 1 litro"),
    ("P008", "Limpiador", "Multiuso ECS 40 x 20 litros"),
    ("P009", "Regulador PH", "Dampsatar / C404"),
    ("P010", "Limpiador", "Limpiamanos x 5 Kg"),
    ("P011", "Polvo", "Antirrepinte x 1 Kg"),
    ("P012", "Adhesivo", "Cola Adheblock x 6 Kg"),
    ("P013", "Limpiador", "Multiuso ECS 40 x 200 litros"),
    ("P014", "Reductor", "Pasta en gel"),
    ("P015", "Embalaje", "Streech"),
    ("P016", "Antisecante", "Aerosol para tintero"),
    ("P017", "Limpiador", "Cleaner (fuerte)"),
    ("P018", "Cauchos", "Ryobi x unidad"),
    ("P019", "Aceite", "Hidrocel x 20 ltrs"),
    ("P020", "Cauchos", "Speed x unidad"),
    ("P021", "Folios", "Tintero Speed x unidad"),
    ("P022", "Limpiador", "Tinner x 1 Litro"),
    ("P023", "Limpiador", "Guantes"),
    ("P024", "Aceite", "Engranaje 150 x 20 Litros"),
    ("P025", "Tintas", "Blanco Transparente x 1 kg"),
    ("P026", "Barniz", "Brillo x 1 kg"),
    ("P027", "Barniz", "Mate x 1 kg"),
]

def transformar_insumo(codigo, insumo, descripcion_excel):
    """
    Aplica las reglas que definiste:
    - Si es Tintas:
        nombre = color  (parte antes de la 'x')
        descripcion = peso (parte después de la 'x', sin la 'x')
    - Si NO es Tintas:
        nombre = insumo
        descripcion = descripcion_excel tal cual
    """
    if insumo.strip().lower() == "tintas":
        partes = descripcion_excel.split("x", 1)
        if len(partes) == 2:
            color = partes[0].strip()
            peso = partes[1].strip()
        else:
            color = descripcion_excel.strip()
            peso = ""

        nombre = color
        descripcion = peso
    else:
        nombre = insumo.strip()
        descripcion = descripcion_excel.strip()

    # Por ahora dejamos unidad en blanco; más adelante la podemos derivar
    unidad = ""
    return codigo, nombre, descripcion, unidad

def cargar_insumos():
    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()

    for codigo, insumo, descripcion_excel in INSUMOS_ORIGINALES:
        codigo_db, nombre_db, descripcion_db, unidad_db = transformar_insumo(
            codigo, insumo, descripcion_excel
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO insumos (codigo, nombre, descripcion, unidad)
            VALUES (?, ?, ?, ?)
            """,
            (codigo_db, nombre_db, descripcion_db, unidad_db),
        )

        print(f"Cargado: {codigo_db} | {nombre_db} | {descripcion_db}")

    conn.commit()
    conn.close()
    print("Carga masiva de insumos finalizada.")


if __name__ == "__main__":
    cargar_insumos()
