import sqlite3
from collections import Counter
from datetime import datetime
from sqlite3 import IntegrityError


from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route("/insumos/nuevo", methods=["POST"])
def insumo_nuevo():
    data = request.get_json(force=True)

    codigo = (data.get("codigo") or "").strip().upper()
    nombre = (data.get("nombre") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    unidad = (data.get("unidad") or "").strip()
    stock_inicial = int(data.get("stock_inicial") or 0)

    if not codigo or not nombre:
        return {"ok": False, "error": "Código e insumo son obligatorios."}, 400

    conn = get_db_connection()
    try:
        # Insertar insumo
        conn.execute(
            "INSERT INTO insumos (codigo, nombre, descripcion, unidad) VALUES (?, ?, ?, ?)",
            (codigo, nombre, descripcion, unidad),
        )
        # Insertar inventario asociado
        cur_inv = conn.execute(
            """
            INSERT INTO inventario (insumo_codigo, stock_inicial, entradas, salidas, total)
            VALUES (?, ?, 0, 0, ?)
            """,
            (codigo, stock_inicial, stock_inicial),
        )
        inv_id = cur_inv.lastrowid
        conn.commit()
    except IntegrityError:
        conn.close()
        return {"ok": False, "error": "Ya existe un insumo con ese código."}, 400

    conn.close()
    return {
        "ok": True,
        "inventario_id": inv_id,
        "codigo": codigo,
        "nombre": nombre,
        "descripcion": descripcion,
        "stock_inicial": stock_inicial,
        "entradas": 0,
        "salidas": 0,
        "total": stock_inicial,
    }, 201

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

    contador_nombres = Counter(f["nombre"] for f in filas)
    insumos = []

    for f in filas:
        codigo = f["codigo"]
        nombre = f["nombre"]
        descripcion = f["descripcion"] or ""

        # Prefijo "Tinta" para las tintas
        if codigo in ("P001", "P002", "P003", "P004", "P025"):
            base_nombre = f"Tinta {nombre}"
        else:
            base_nombre = nombre

        # Si hay nombres repetidos, agregamos descripción
        if contador_nombres[nombre] > 1 and descripcion:
            nombre_mostrar = f"{base_nombre} {descripcion}"
        else:
            nombre_mostrar = base_nombre

        insumos.append(
            {
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": descripcion,
                "nombre_mostrar": nombre_mostrar,
            }
        )

    insumos.sort(key=lambda x: x["nombre_mostrar"])
    return insumos


# ---------------- RUTAS PRINCIPALES ----------------

@app.route("/")
def menu_principal():
    return render_template("base.html", vista="menu")


@app.route("/inventario")
def inventario():
    conn = get_db_connection()
    registros = conn.execute("""
        SELECT inv.id,
               inv.insumo_codigo AS codigo,
               ins.nombre,
               ins.descripcion,
               inv.stock_inicial,
               inv.entradas,
               inv.salidas,
               inv.total
        FROM inventario inv
        JOIN insumos ins ON inv.insumo_codigo = ins.codigo
        ORDER BY ins.nombre
    """).fetchall()
    conn.close()
    return render_template("base.html", vista="inventario", registros=registros)


@app.route("/entradas")
def entradas():
    return render_template("base.html", vista="entradas")


@app.route("/salidas")
def salidas():
    return render_template("base.html", vista="salidas")


@app.route("/pedidos")
def pedidos():
    return render_template("base.html", vista="pedidos")


# ---------------- ENTRADAS ----------------

@app.route("/entradas/nueva", methods=["GET", "POST"])
def entradas_nueva():
    if request.method == "POST":
        insumo_codigo = request.form.get("insumo_seleccionado")
        cantidad = request.form.get("unidad_seleccionada")

        if not insumo_codigo or not cantidad:
            insumos = obtener_insumos()
            return render_template("base.html", vista="entradas_nueva",
                                   insumos=insumos, registro_ok=False)

        cantidad_int = int(cantidad)
        conn = get_db_connection()
        fecha = datetime.now().strftime("%d-%b")

        # Insertar en entradas
        conn.execute(
            "INSERT INTO entradas (fecha, insumo_codigo, cantidad) VALUES (?, ?, ?)",
            (fecha, insumo_codigo, cantidad_int),
        )

        # Actualizar inventario: sumar entradas y total
        conn.execute("""
            UPDATE inventario
            SET entradas = entradas + ?, total = total + ?
            WHERE insumo_codigo = ?
        """, (cantidad_int, cantidad_int, insumo_codigo))

        conn.commit()
        conn.close()

        return redirect(url_for("entradas_nueva", ok="1"))

    insumos = obtener_insumos()
    registro_ok = request.args.get("ok") == "1"
    return render_template("base.html", vista="entradas_nueva",
                           insumos=insumos, registro_ok=registro_ok)


@app.route("/entradas/historial")
def entradas_historial():
    conn = get_db_connection()
    registros = conn.execute(
        """
        SELECT e.id, e.fecha, i.codigo, i.nombre, i.descripcion, e.cantidad
        FROM entradas e
        JOIN insumos i ON e.insumo_codigo = i.codigo
        ORDER BY e.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template(
        "base.html", vista="entradas_historial", registros=registros
    )


@app.route("/entradas/<int:registro_id>/borrar", methods=["POST"])
def borrar_entrada(registro_id: int):
    conn = get_db_connection()
    conn.execute("DELETE FROM entradas WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()
    return ("", 204)


# ---------------- SALIDAS ----------------

@app.route("/salidas/nueva", methods=["GET", "POST"])
def salidas_nueva():
    if request.method == "POST":
        insumo_codigo = request.form.get("insumo_seleccionado")
        cantidad = request.form.get("unidad_seleccionada")

        if not insumo_codigo or not cantidad:
            insumos = obtener_insumos()
            return render_template("base.html", vista="salidas_nueva",
                                   insumos=insumos, registro_ok=False)

        cantidad_int = int(cantidad)
        conn = get_db_connection()
        fecha = datetime.now().strftime("%d-%b")

        conn.execute(
            "INSERT INTO salidas (fecha, insumo_codigo, cantidad) VALUES (?, ?, ?)",
            (fecha, insumo_codigo, cantidad_int),
        )

        # Actualizar inventario: sumar salidas y restar al total
        conn.execute("""
            UPDATE inventario
            SET salidas = salidas + ?, total = total - ?
            WHERE insumo_codigo = ?
        """, (cantidad_int, cantidad_int, insumo_codigo))

        conn.commit()
        conn.close()

        return redirect(url_for("salidas_nueva", ok="1"))

    insumos = obtener_insumos()
    registro_ok = request.args.get("ok") == "1"
    return render_template("base.html", vista="salidas_nueva",
                           insumos=insumos, registro_ok=registro_ok)




@app.route("/salidas/historial")
def salidas_historial():
    conn = get_db_connection()
    registros = conn.execute(
        """
        SELECT s.id, s.fecha, i.codigo, i.nombre, i.descripcion, s.cantidad
        FROM salidas s
        JOIN insumos i ON s.insumo_codigo = i.codigo
        ORDER BY s.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template(
        "base.html", vista="salidas_historial", registros=registros
    )


@app.route("/salidas/<int:registro_id>/borrar", methods=["POST"])
def borrar_salida(registro_id: int):
    conn = get_db_connection()
    conn.execute("DELETE FROM salidas WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()
    return ("", 204)

@app.route("/inventario/<int:item_id>/actualizar", methods=["POST"])
def inventario_actualizar(item_id: int):
    data = request.get_json(force=True)
    stock_inicial = int(data.get("stock_inicial", 0))
    entradas = int(data.get("entradas", 0))
    salidas = int(data.get("salidas", 0))
    total = int(data.get("total", stock_inicial + entradas - salidas))

    conn = get_db_connection()
    conn.execute("""
        UPDATE inventario
        SET stock_inicial = ?, entradas = ?, salidas = ?, total = ?
        WHERE id = ?
    """, (stock_inicial, entradas, salidas, total, item_id))
    conn.commit()
    conn.close()

    return {"ok": True}, 200


# ---------------- ARRANQUE APP ----------------

if __name__ == "__main__":
    print("Levantando servidor Flask en http://127.0.0.1:5000/")
    app.run(debug=True)
