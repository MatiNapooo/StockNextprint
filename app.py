import sqlite3
from collections import Counter
from datetime import datetime
from sqlite3 import IntegrityError
from flask import Flask, render_template, request, redirect, url_for, session


app = Flask(__name__)
# Clave para firmar la cookie de sesión (podés cambiarla por otra)
app.secret_key = "nextprint-stock-super-secreto"

# Usuarios habilitados para ADMIN
USUARIOS_ADMIN = {
    "nnapoli": "matiesmihijofavorito",
    "luis": "nnapoli",
}


def credenciales_validas(usuario, contrasena):
    if not usuario or not contrasena:
        return False
    esperado = USUARIOS_ADMIN.get(usuario.strip())
    return esperado is not None and esperado == contrasena.strip()


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


@app.route("/insumos/<codigo>/actualizar", methods=["POST"])
def insumo_actualizar(codigo):
    data = request.get_json(force=True)
    nuevo_codigo = (data.get("codigo") or "").strip().upper()
    nombre = (data.get("nombre") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    unidad = (data.get("unidad") or "").strip()

    if not nuevo_codigo or not nombre:
        return {"ok": False, "error": "Código e insumo son obligatorios."}, 400

    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE insumos
            SET codigo = ?, nombre = ?, descripcion = ?, unidad = ?
            WHERE codigo = ?
        """, (nuevo_codigo, nombre, descripcion, unidad, codigo))

        conn.execute("""
            UPDATE inventario
            SET insumo_codigo = ?
            WHERE insumo_codigo = ?
        """, (nuevo_codigo, codigo))

        conn.execute("""
            UPDATE entradas
            SET insumo_codigo = ?
            WHERE insumo_codigo = ?
        """, (nuevo_codigo, codigo))

        conn.execute("""
            UPDATE salidas
            SET insumo_codigo = ?
            WHERE insumo_codigo = ?
        """, (nuevo_codigo, codigo))

        conn.commit()
    except IntegrityError:
        conn.close()
        return {"ok": False, "error": "Ya existe un insumo con ese código."}, 400

    conn.close()
    return {"ok": True}, 200


def get_db_connection():
    conn = sqlite3.connect("stock.db")
    conn.row_factory = sqlite3.Row
    return conn

def obtener_registros_inventario():
    conn = get_db_connection()
    filas = conn.execute("""
        SELECT inv.id,
               inv.insumo_codigo AS codigo,
               ins.nombre,
               ins.descripcion,
               ins.unidad,
               inv.stock_inicial,
               inv.entradas,
               inv.salidas,
               inv.total
        FROM inventario inv
        JOIN insumos ins ON inv.insumo_codigo = ins.codigo
    """).fetchall()
    conn.close()

    # Ajuste de nombres (Tinta + color) y orden alfabético
    contador_nombres = Counter(f["nombre"] for f in filas)
    registros = []

    for f in filas:
        d = dict(f)
        codigo = d["codigo"]
        nombre = d["nombre"]
        descripcion = d["descripcion"] or ""

        # Prefijo "Tinta" para las tintas
        if codigo in ("P001", "P002", "P003", "P004", "P025"):
            base_nombre = f"Tinta {nombre}"
        else:
            base_nombre = nombre

        if contador_nombres[nombre] > 1 and descripcion:
            nombre_mostrar = f"{base_nombre} {descripcion}"
        else:
            nombre_mostrar = base_nombre

        d["nombre"] = nombre_mostrar
        registros.append(d)

    registros.sort(key=lambda x: x["nombre"])
    return registros

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

from collections import Counter  # ponlo arriba si todavía no lo importaste

# ---------------------------------------------------------
# INVENTARIO: función auxiliar que devuelve los registros
# ---------------------------------------------------------
def obtener_registros_inventario():
    conn = get_db_connection()
    filas = conn.execute(
        """
        SELECT inv.id,
               inv.insumo_codigo AS codigo,
               ins.nombre,
               ins.descripcion,
               ins.unidad,
               inv.stock_inicial,
               inv.entradas,
               inv.salidas,
               inv.total
        FROM inventario inv
        JOIN insumos ins ON inv.insumo_codigo = ins.codigo
        """
    ).fetchall()
    conn.close()

    contador_nombres = Counter(f["nombre"] for f in filas)
    registros = []

    for f in filas:
        d = dict(f)
        codigo = d["codigo"]
        nombre = d["nombre"]
        descripcion = d["descripcion"] or ""

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

        d["nombre"] = nombre_mostrar
        registros.append(d)

    # Orden alfabético por nombre a mostrar
    registros.sort(key=lambda x: x["nombre"])
    return registros


# ---------------------------------------------------------
# ADMIN (vista actual de inventario, con botones)
# ---------------------------------------------------------
@app.route("/inventario", methods=["GET", "POST"])
def inventario():
    # Si ya hay sesión de admin activa en este navegador,
    # mostramos directamente el inventario ADMIN.
    if session.get("usuario_admin"):
        registros = obtener_registros_inventario()
        return render_template("base.html", vista="inventario", registros=registros)

    # Si no hay sesión, procesamos login
    error = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "").strip()

        if credenciales_validas(usuario, contrasena):
            # Guardamos usuario en la sesión de este navegador
            session["usuario_admin"] = usuario
            registros = obtener_registros_inventario()
            return render_template("base.html", vista="inventario", registros=registros)
        else:
            error = "Usuario o contraseña incorrecta"

    # GET inicial o POST fallido → mostrar formulario de login
    return render_template("base.html", vista="login_admin", login_error=error)


@app.route("/logout_admin")
def logout_admin():
    # Borrar el usuario de la sesión de este navegador
    session.pop("usuario_admin", None)
    # Volver a /inventario, que ahora mostrará el login
    return redirect(url_for("inventario"))



# ---------------------------------------------------------
# INVENTARIO (solo lectura, sin botones)
# ---------------------------------------------------------
@app.route("/inventario_simple")
def inventario_simple():
    registros = obtener_registros_inventario()
    return render_template("base.html", vista="inventario_simple", registros=registros)


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

        # Validación: si falta algo, volvemos a mostrar el formulario
        if not insumo_codigo or not cantidad:
            insumos = obtener_insumos()
            return render_template(
                "base.html",
                vista="entradas_nueva",
                insumos=insumos,
                registro_ok=False,
            )

        cantidad_int = int(cantidad)
        conn = get_db_connection()
        fecha = datetime.now().strftime("%d-%b")

        # Guardar entrada
        conn.execute(
            "INSERT INTO entradas (fecha, insumo_codigo, cantidad) VALUES (?, ?, ?)",
            (fecha, insumo_codigo, cantidad_int),
        )

        # Actualizar inventario: sumar entradas y recalcular total
        conn.execute(
            """
            UPDATE inventario
            SET entradas = entradas + ?,
                total = stock_inicial + (entradas + ?) - salidas
            WHERE insumo_codigo = ?
            """,
            (cantidad_int, cantidad_int, insumo_codigo),
        )

        conn.commit()
        conn.close()

        # Redirigimos con ?ok=1 para mostrar el popup "Registro confirmado"
        return redirect(url_for("entradas_nueva", ok="1"))

    # GET: mostrar formulario
    insumos = obtener_insumos()
    registro_ok = request.args.get("ok") == "1"
    return render_template(
        "base.html",
        vista="entradas_nueva",
        insumos=insumos,
        registro_ok=registro_ok,
    )




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

        # Validación: si falta algo, volvemos a mostrar el formulario
        if not insumo_codigo or not cantidad:
            insumos = obtener_insumos()
            return render_template(
                "base.html",
                vista="salidas_nueva",
                insumos=insumos,
                registro_ok=False,
            )

        cantidad_int = int(cantidad)
        conn = get_db_connection()
        fecha = datetime.now().strftime("%d-%b")

        # Guardar salida
        conn.execute(
            "INSERT INTO salidas (fecha, insumo_codigo, cantidad) VALUES (?, ?, ?)",
            (fecha, insumo_codigo, cantidad_int),
        )

        # Actualizar inventario: sumar salidas y recalcular total
        conn.execute(
            """
            UPDATE inventario
            SET salidas = salidas + ?,
                total = stock_inicial + entradas - (salidas + ?)
            WHERE insumo_codigo = ?
            """,
            (cantidad_int, cantidad_int, insumo_codigo),
        )

        conn.commit()
        conn.close()

        # Redirigimos con ?ok=1 para mostrar el popup "Registro confirmado"
        return redirect(url_for("salidas_nueva", ok="1"))

    # GET: mostrar formulario
    insumos = obtener_insumos()
    registro_ok = request.args.get("ok") == "1"
    return render_template(
        "base.html",
        vista="salidas_nueva",
        insumos=insumos,
        registro_ok=registro_ok,
    )





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

    total = stock_inicial + entradas - salidas

    conn = get_db_connection()
    conn.execute("""
        UPDATE inventario
        SET stock_inicial = ?, entradas = ?, salidas = ?, total = ?
        WHERE id = ?
    """, (stock_inicial, entradas, salidas, total, item_id))
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "stock_inicial": stock_inicial,
        "entradas": entradas,
        "salidas": salidas,
        "total": total,
    }, 200

@app.route("/insumos/<codigo>/eliminar", methods=["POST"])
def insumo_eliminar(codigo):
    codigo = codigo.strip().upper()
    conn = get_db_connection()

    # Borramos movimientos e inventario asociados
    conn.execute("DELETE FROM entradas WHERE insumo_codigo = ?", (codigo,))
    conn.execute("DELETE FROM salidas WHERE insumo_codigo = ?", (codigo,))
    conn.execute("DELETE FROM inventario WHERE insumo_codigo = ?", (codigo,))
    conn.execute("DELETE FROM insumos WHERE codigo = ?", (codigo,))

    conn.commit()
    conn.close()
    return {"ok": True}, 200

@app.route("/insumos/modificar", methods=["POST"])
def insumo_modificar():
    data = request.get_json(force=True)

    codigo_original = (data.get("codigo_original") or "").strip().upper()
    codigo_nuevo = (data.get("codigo_nuevo") or "").strip().upper()
    nombre = (data.get("nombre") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    unidad = (data.get("unidad") or "").strip()

    if not codigo_original or not codigo_nuevo or not nombre:
        return {"ok": False, "error": "Código e insumo son obligatorios."}, 400

    conn = get_db_connection()
    try:
        fila_inv = conn.execute(
            "SELECT id FROM inventario WHERE insumo_codigo = ?",
            (codigo_original,),
        ).fetchone()
        inventario_id = fila_inv["id"] if fila_inv else None

        conn.execute("""
            UPDATE insumos
            SET codigo = ?, nombre = ?, descripcion = ?, unidad = ?
            WHERE codigo = ?
        """, (codigo_nuevo, nombre, descripcion, unidad, codigo_original))

        conn.execute(
            "UPDATE inventario SET insumo_codigo = ? WHERE insumo_codigo = ?",
            (codigo_nuevo, codigo_original),
        )
        conn.execute(
            "UPDATE entradas SET insumo_codigo = ? WHERE insumo_codigo = ?",
            (codigo_nuevo, codigo_original),
        )
        conn.execute(
            "UPDATE salidas SET insumo_codigo = ? WHERE insumo_codigo = ?",
            (codigo_nuevo, codigo_original),
        )

        conn.commit()
    except IntegrityError:
        conn.rollback()
        conn.close()
        return {"ok": False, "error": "Ya existe un insumo con ese código."}, 400

    conn.close()
    return {
        "ok": True,
        "codigo": codigo_nuevo,
        "nombre": nombre,
        "descripcion": descripcion,
        "unidad": unidad,
        "inventario_id": inventario_id,
    }, 200




# ---------------- ARRANQUE APP ----------------

if __name__ == "__main__":
    print("Levantando servidor Flask en http://127.0.0.1:5000/")
    app.run(debug=True)
