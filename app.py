import sqlite3
from collections import Counter
from flask import Flask, render_template

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect("stock.db")
    conn.row_factory = sqlite3.Row
    return conn

def obtener_insumos():
    conn = get_db_connection()
    filas = conn.execute(
        "SELECT codigo, nombre, descripcion FROM insumos"
    ).fetchall()
    conn.close()

    # Contar cuántos insumos tienen el mismo nombre
    contador_nombres = Counter(f["nombre"] for f in filas)

    insumos = []
    for f in filas:
        codigo = f["codigo"]
        nombre = f["nombre"]
        descripcion = f["descripcion"] or ""

        # 1) Prefijo "Tinta" para las tintas (según código)
        if codigo in ("P001", "P002", "P003", "P004", "P025"):
            base_nombre = f"Tinta {nombre}"
        else:
            base_nombre = nombre

        # 2) Si hay más de un insumo con el mismo nombre,
        #    agregamos la descripción para diferenciarlos
        if contador_nombres[nombre] > 1 and descripcion:
            nombre_mostrar = f"{base_nombre} {descripcion}"
        else:
            nombre_mostrar = base_nombre

        insumos.append({
            "codigo": codigo,
            "nombre": nombre,
            "descripcion": descripcion,
            "nombre_mostrar": nombre_mostrar,
        })

    # Ordenamos por el nombre que se muestra
    insumos.sort(key=lambda x: x["nombre_mostrar"])
    return insumos
@app.route("/")
def home():
    return render_template("base.html", vista="home")

@app.route("/inventario")
def inventario():
    return render_template("base.html", vista="inventario")

@app.route("/entradas")
def entradas():
    return render_template("base.html", vista="entradas")

@app.route("/entradas/nueva")
def entradas_nueva():
    insumos = obtener_insumos()
    return render_template("base.html", vista="entradas_nueva", insumos=insumos)

@app.route("/salidas")
def salidas():
    return render_template("base.html", vista="salidas")

@app.route("/salidas/nueva")
def salidas_nueva():
    insumos = obtener_insumos()
    return render_template("base.html", vista="salidas_nueva", insumos=insumos)

@app.route("/pedidos")
def pedidos():
    return render_template("base.html", vista="pedidos")

@app.route("/pedidos/nuevo")
def pedidos_nuevo():
    return render_template("base.html", vista="pedidos_nuevo")

if __name__ == "__main__":
    app.run(debug=True)
