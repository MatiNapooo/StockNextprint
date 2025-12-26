import sqlite3
import os 
from collections import Counter
from datetime import datetime
from sqlite3 import IntegrityError
from flask import Flask, render_template, request, redirect, url_for, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "stock.db")  # <-- USAR ESTA (ES LA QUE TIENE DATOS)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
# Clave para firmar la cookie de sesión (podés cambiarla por otra)
app.secret_key = "nextprint-stock-super-secreto"


# Usuarios habilitados para ADMIN
USERS = {
    "nicolas": "nnapoli",
    "luis": "lonapoli",
}


def credenciales_validas(usuario, contrasena):
    if not usuario or not contrasena:
        return False
    esperado = USERS.get(usuario.strip())
    return esperado is not None and esperado == contrasena.strip()


def inventario_rows(conn):
    # Inventario calculado (insumos + sumatorias entradas/salidas)
    return conn.execute("""
        SELECT
            i.codigo,
            i.insumo,
            i.descripcion,
            COALESCE(i.stock_inicial, 0) AS stock_inicial,
            COALESCE(e.entradas, 0) AS entradas,
            COALESCE(s.salidas, 0) AS salidas,
            (COALESCE(i.stock_inicial, 0) + COALESCE(e.entradas, 0) - COALESCE(s.salidas, 0)) AS total
        FROM insumos i
        LEFT JOIN (
            SELECT codigo, SUM(cantidad) AS entradas
            FROM entradas
            GROUP BY codigo
        ) e ON e.codigo = i.codigo
        LEFT JOIN (
            SELECT codigo, SUM(cantidad) AS salidas
            FROM salidas
            GROUP BY codigo
        ) s ON s.codigo = i.codigo
        ORDER BY i.insumo COLLATE NOCASE
    """).fetchall()


def inventario_row_by_codigo(conn, codigo):
    row = conn.execute("""
        SELECT
            i.codigo,
            i.insumo,
            i.descripcion,
            COALESCE(i.stock_inicial, 0) AS stock_inicial,
            COALESCE(e.entradas, 0) AS entradas,
            COALESCE(s.salidas, 0) AS salidas,
            (COALESCE(i.stock_inicial, 0) + COALESCE(e.entradas, 0) - COALESCE(s.salidas, 0)) AS total
        FROM insumos i
        LEFT JOIN (
            SELECT codigo, SUM(cantidad) AS entradas
            FROM entradas
            GROUP BY codigo
        ) e ON e.codigo = i.codigo
        LEFT JOIN (
            SELECT codigo, SUM(cantidad) AS salidas
            FROM salidas
            GROUP BY codigo
        ) s ON s.codigo = i.codigo
        WHERE i.codigo = ?
    """, (codigo,)).fetchone()
    return row

# --------- LOGIN ADMIN (INSUMOS) ----------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    # Si ya está logueado, mostrar inventario admin
    if request.method == "GET":
        if session.get("admin_logged_in"):
            return redirect(url_for("admin_inventario"))
        return render_template("base.html", vista="admin_login", login_error=False)

    # POST: intentar login
    usuario = (request.form.get("usuario") or "").strip()
    contrasena = request.form.get("contrasena") or ""

    if USERS.get(usuario) == contrasena:
        session.clear()
        session["admin_logged_in"] = True
        session["admin_user"] = usuario
        session.permanent = False  # cookie de sesión (no permanente)
        return redirect(url_for("admin_inventario"))

    return render_template("base.html", vista="admin_login", login_error=True)


@app.route("/admin/inventario")
def admin_inventario():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_conn()
    registros = inventario_rows(conn)
    conn.close()
    return render_template("base.html", vista="inventario_admin", registros=registros)


@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect(url_for("admin"))


# --------- LOGIN ADMIN PAPEL ----------
@app.route("/papel/admin", methods=["GET", "POST"])
def papel_admin():
    error = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "").strip()

        cred_ok = (
            (usuario == "nicolas" and contrasena == "nnapoli") or
            (usuario == "luis" and contrasena == "lonapoli")
        )

        if cred_ok:
            session["papel_admin_logueado"] = True
        else:
            error = "Usuario o contraseña incorrecta"

    if not session.get("papel_admin_logueado"):
        return render_template("base.html", vista="admin_login", modo="papel", error=error)

    # inventario SIMPLE de papel cuando está logueado
    conn = get_conn()
    registros = conn.execute("""
        SELECT * FROM inventario
        ORDER BY insumo_codigo
    """).fetchall()

    conn.close()

    return render_template(
        "base.html",
        vista="papel_inventario_admin",   # otro bloque de tabla para papel
        modo="papel",
        registros=registros
    )


# --------- LOGOUT (cierra ambas sesiones) ----------
@app.route("/logout")
def logout():
    session.pop("admin_logueado", None)
    session.pop("papel_admin_logueado", None)
    return redirect(url_for("admin"))

@app.route("/insumos/<codigo>/actualizar", methods=["POST"])
def insumo_actualizar(codigo):
    data = request.get_json(force=True)
    nuevo_codigo = (data.get("codigo") or "").strip().upper()
    nombre = (data.get("nombre") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    unidad = (data.get("unidad") or "").strip()

    if not nuevo_codigo or not nombre:
        return {"ok": False, "error": "Código e insumo son obligatorios."}, 400

    conn = get_conn()
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


def obtener_registros_inventario():
    conn = get_conn()
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
    conn = get_conn()
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
            session.permanent = True  # Sesión persiste hasta que haga logout explícito
            session["usuario_admin"] = usuario
            registros = obtener_registros_inventario()
            return render_template("base.html", vista="inventario", registros=registros)
        else:
            error = "Usuario o contraseña incorrecta"

    # GET inicial o POST fallido → mostrar formulario de login
    return render_template("base.html", vista="admin_login", login_error=error)

# ---------- PAPEL: INVENTARIO SIMPLE ----------
@app.route("/papel/inventario")
def papel_inventario():
    conn = get_conn()
    registros = conn.execute("""
        SELECT id, nombre, stock_inicial, entradas, salidas, total
        FROM papel_inventario
        ORDER BY nombre
    """).fetchall()
    conn.close()
    return render_template(
        "base.html",
        vista="papel_inventario_simple",   # <<< nombre de vista para el simple
        registros=registros,
        modo="papel"
    )


# ---------------------------------------------------------
# INVENTARIO (solo lectura, sin botones)
# ---------------------------------------------------------
@app.route("/inventario_simple")
def inventario_simple():
    registros = obtener_registros_inventario()
    return render_template("base.html", vista="inventario_simple", registros=registros)



@app.route("/entradas")
def entradas_menu():
    return render_template("base.html", vista="entradas_menu")


@app.route("/salidas")
def salidas_menu():
    return render_template("base.html", vista="salidas_menu")


@app.route("/entradas/nuevo")
def entradas_nuevo():
    conn = get_conn()
    insumos = conn.execute("""
        SELECT codigo, nombre, descripcion
        FROM insumos
        ORDER BY nombre COLLATE NOCASE
    """).fetchall()
    conn.close()
    return render_template("base.html", vista="mov_nuevo", mov_tipo="entrada", insumos=insumos)


@app.route("/salidas/nuevo")
def salidas_nuevo():
    conn = get_conn()
    insumos = conn.execute("""
        SELECT codigo, nombre, descripcion
        FROM insumos
        ORDER BY nombre COLLATE NOCASE
    """).fetchall()
    conn.close()
    return render_template("base.html", vista="mov_nuevo", mov_tipo="salida", insumos=insumos)


@app.route("/entradas/historial")
def entradas_historial():
    conn = get_conn()
    registros = conn.execute("""
        SELECT id, fecha, codigo, insumo, descripcion, cantidad
        FROM entradas
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return render_template("base.html", vista="mov_historial", mov_tipo="entrada", registros=registros)


@app.route("/salidas/historial")
def salidas_historial():
    conn = get_conn()
    registros = conn.execute("""
        SELECT id, fecha, codigo, insumo, descripcion, cantidad
        FROM salidas
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return render_template("base.html", vista="mov_historial", mov_tipo="salida", registros=registros)


@app.post("/api/movimiento/preview")
def api_mov_preview():
    data = request.get_json(silent=True) or {}
    tipo = (data.get("tipo") or "").strip().lower()
    codigo = (data.get("codigo") or "").strip()
    cantidad_raw = data.get("cantidad")

    if tipo not in ("entrada", "salida"):
        return jsonify(ok=False, error="Tipo inválido."), 400
    if not codigo:
        return jsonify(ok=False, error="Tenés que elegir un insumo."), 400
    try:
        cantidad = int(cantidad_raw)
        if cantidad <= 0:
            raise ValueError()
    except Exception:
        return jsonify(ok=False, error="Tenés que elegir una cantidad válida."), 400

    conn = get_conn()
    row = inventario_row_by_codigo(conn, codigo)
    conn.close()

    if not row:
        return jsonify(ok=False, error="No existe el insumo seleccionado."), 404

    stock_inicial = int(row["stock_inicial"])
    entradas = int(row["entradas"])
    salidas = int(row["salidas"])
    total_actual = int(row["total"])

    if tipo == "entrada":
        entradas_nuevo = entradas + cantidad
        salidas_nuevo = salidas
        total_nuevo = total_actual + cantidad
    else:
        entradas_nuevo = entradas
        salidas_nuevo = salidas + cantidad
        total_nuevo = total_actual - cantidad

    preview = {
        "codigo": row["codigo"],
        "insumo": row["insumo"],
        "descripcion": row["descripcion"],
        "stock_inicial": stock_inicial,
        "entradas": entradas_nuevo,
        "salidas": salidas_nuevo,
        "total": total_nuevo,
        "cantidad_mov": cantidad,
        "tipo": tipo,
    }
    return jsonify(ok=True, preview=preview)


@app.post("/api/movimiento/confirm")
def api_mov_confirm():
    data = request.get_json(silent=True) or {}
    tipo = (data.get("tipo") or "").strip().lower()
    codigo = (data.get("codigo") or "").strip()
    cantidad_raw = data.get("cantidad")

    if tipo not in ("entrada", "salida"):
        return jsonify(ok=False, error="Tipo inválido."), 400
    if not codigo:
        return jsonify(ok=False, error="Tenés que elegir un insumo."), 400
    try:
        cantidad = int(cantidad_raw)
        if cantidad <= 0:
            raise ValueError()
    except Exception:
        return jsonify(ok=False, error="Tenés que elegir una cantidad válida."), 400

    conn = get_conn()
    ins = conn.execute("SELECT codigo, insumo, descripcion FROM insumos WHERE codigo = ?", (codigo,)).fetchone()
    if not ins:
        conn.close()
        return jsonify(ok=False, error="No existe el insumo seleccionado."), 404

    fecha = datetime.now().strftime("%Y-%m-%d")

    if tipo == "entrada":
        conn.execute(
            "INSERT INTO entradas (fecha, codigo, insumo, descripcion, cantidad) VALUES (?,?,?,?,?)",
            (fecha, ins["codigo"], ins["insumo"], ins["descripcion"], cantidad),
        )
    else:
        conn.execute(
            "INSERT INTO salidas (fecha, codigo, insumo, descripcion, cantidad) VALUES (?,?,?,?,?)",
            (fecha, ins["codigo"], ins["insumo"], ins["descripcion"], cantidad),
        )

    conn.commit()
    conn.close()

    return jsonify(ok=True, cantidad=cantidad)


@app.post("/api/movimiento/delete")
def api_mov_delete():
    data = request.get_json(silent=True) or {}
    tipo = (data.get("tipo") or "").strip().lower()
    mov_id = data.get("id")

    if tipo not in ("entrada", "salida"):
        return jsonify(ok=False, error="Tipo inválido."), 400
    try:
        mov_id = int(mov_id)
    except Exception:
        return jsonify(ok=False, error="ID inválido."), 400

    tabla = "entradas" if tipo == "entrada" else "salidas"
    conn = get_conn()
    conn.execute(f"DELETE FROM {tabla} WHERE id = ?", (mov_id,))
    conn.commit()
    conn.close()

    return jsonify(ok=True)



@app.route("/inventario/<int:item_id>/actualizar", methods=["POST"])
def inventario_actualizar(item_id: int):
    data = request.get_json(force=True)
    stock_inicial = int(data.get("stock_inicial", 0))
    entradas = int(data.get("entradas", 0))
    salidas = int(data.get("salidas", 0))

    total = stock_inicial + entradas - salidas

    conn = get_conn()
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
    conn = get_conn()

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

    conn = get_conn()
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

@app.route("/insumo/agregar", methods=["POST"])
def insumo_agregar():
    data = request.get_json()
    codigo = (data.get("codigo") or "").strip()
    nombre = (data.get("nombre") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    unidad = (data.get("unidad") or "").strip()
    stock = int(data.get("stock") or 0)

    if not codigo or not nombre or not descripcion:
        return ("Faltan datos", 400)

    conn = get_conn()

    # Insertar en insumos
    conn.execute("""
        INSERT INTO insumos (codigo, nombre, descripcion, proveedor, unidad)
        VALUES (?, ?, ?, '', ?)
    """, (codigo, nombre, descripcion, unidad))

    # Insertar/asegurar inventario
    existe = conn.execute("SELECT 1 FROM inventario WHERE insumo_codigo = ?", (codigo,)).fetchone()
    if not existe:
        conn.execute("""
            INSERT INTO inventario (insumo_codigo, stock_inicial, entradas, salidas, total)
            VALUES (?, ?, 0, 0, ?)
        """, (codigo, stock, stock))
    else:
        conn.execute("""
            UPDATE inventario
            SET stock_inicial = stock_inicial + ?, total = total + ?
            WHERE insumo_codigo = ?
        """, (stock, stock, codigo))

    conn.commit()
    conn.close()
    return ("OK", 200)

# -------------------------
# PEDIDOS
# -------------------------

@app.route("/pedidos")
def pedidos():
    # Menú de pedidos: ver historial / registrar nuevo
    return render_template("base.html", vista="pedidos")


@app.route("/pedidos/nuevo", methods=["GET", "POST"])
def pedidos_nuevo():
    if request.method == "POST":
        pedido_por = request.form.get("pedido_por", "").strip()
        proveedor = request.form.get("proveedor", "").strip()
        insumo = request.form.get("insumo", "").strip()
        insumo_codigo = request.form.get("insumo_codigo", "").strip()
        presentacion = request.form.get("presentacion", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        cantidad = request.form.get("cantidad", "").strip()

        if not (pedido_por and proveedor and insumo and presentacion and descripcion and cantidad):
            error = "Faltan completar campos"
            # Volver a mostrar el formulario con error
            # (si querés pasar el error al template)
            conn = get_conn()
            insumos = conn.execute(
                "SELECT codigo, nombre, descripcion FROM insumos ORDER BY nombre"
            ).fetchall()
            conn.close()
            return render_template(
                "base.html",
                vista="pedidos_nuevo",
                error=error,
                insumos=insumos,
            )

        conn = get_conn()
        conn.execute(
            """
            INSERT INTO pedidos
                (fecha, pedido_por, proveedor, insumo,
                 presentacion, descripcion, cantidad, estado, insumo_codigo)
            VALUES (DATE('now'), ?, ?, ?, ?, ?, ?, 'En Espera', ?)
            """,
            (pedido_por, proveedor, insumo, presentacion, descripcion, cantidad, insumo_codigo or None),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("pedidos", ok=1))

    # GET → cargar lista de insumos para el datalist
    conn = get_conn()
    insumos = conn.execute(
        "SELECT codigo, nombre, descripcion FROM insumos ORDER BY nombre"
    ).fetchall()
    conn.close()

    return render_template("base.html", vista="pedidos_nuevo", insumos=insumos)


@app.route("/pedidos/historial")
def pedidos_historial():
    conn = get_conn()
    registros = conn.execute(
        """
        SELECT id, fecha, pedido_por, proveedor, insumo,
               presentacion, descripcion, cantidad, estado
        FROM pedidos
        ORDER BY fecha DESC, id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("base.html", vista="pedidos_historial", registros=registros)

@app.route("/pedidos/<int:pedido_id>/entregado", methods=["POST"])
def pedido_entregado(pedido_id):
    conn = get_conn()
    pedido = conn.execute(
        "SELECT cantidad, insumo_codigo, estado FROM pedidos WHERE id = ?",
        (pedido_id,),
    ).fetchone()

    if pedido is None:
        conn.close()
        return redirect(url_for("pedidos_historial"))

    if pedido["estado"] != "Entregado":
        cantidad = pedido["cantidad"]
        insumo_codigo = pedido["insumo_codigo"]

        if insumo_codigo:
            conn.execute(
                """
                UPDATE inventario
                SET stock_inicial = stock_inicial + ?,
                    total = total + ?
                WHERE insumo_codigo = ?
                """,
                (cantidad, cantidad, insumo_codigo),
            )

        conn.execute(
            "UPDATE pedidos SET estado = 'Entregado' WHERE id = ?",
            (pedido_id,),
        )
        conn.commit()

    conn.close()
    return redirect(url_for("pedidos_historial"))



# ---------- PAPEL - MENÚ ENTRADAS ----------
@app.route("/papel/entradas")
def papel_entradas():
    return render_template(
        "base.html",
        vista="papel_entradas_menu",
        modo="papel"
    )

# ---------- PAPEL - REGISTRAR NUEVA ENTRADA ----------
from datetime import datetime

@app.route("/papel/entradas/nuevo", methods=["GET", "POST"])
def papel_entradas_nuevo():
    if request.method == "POST":
        tipo_papel = request.form.get("tipo_papel", "").strip()
        gramaje = request.form.get("gramaje", "").strip()
        formato = request.form.get("formato", "").strip()
        proveedor = request.form.get("proveedor", "").strip()
        marca = request.form.get("marca", "").strip()
        cantidad = request.form.get("cantidad", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        # VALIDACIÓN BÁSICA
        if not tipo_papel or not gramaje or not formato or not proveedor or not marca or not cantidad:
            error = "Tenés que completar todos los campos obligatorios."
            # cargar lista de papeles para volver a mostrar el formulario
            conn = get_conn()
            papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
            conn.close()
            preview = {
                "tipo_papel": tipo_papel,
                "gramaje": gramaje,
                "formato": formato,
                "proveedor": proveedor,
                "marca": marca,
                "cantidad": cantidad,
                "observaciones": observaciones,
            }
            return render_template(
                "base.html",
                vista="papel_entradas_nueva",
                modo="papel",
                error=error,
                papeles=papeles,
                preview=preview,
            )

        # GUARDAR EN BD
        conn = get_conn()
        fecha = datetime.now().strftime("%Y-%m-%d")

        conn.execute("""
            INSERT INTO papel_entradas
                (fecha, tipo_papel, gramaje, formato, proveedor, marca, cantidad, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha, tipo_papel, gramaje, formato, proveedor, marca, cantidad, observaciones))

        conn.commit()
        conn.close()

        # Después de guardar, redirigimos al historial con ?ok=1 para mostrar el popup
        return redirect(url_for("papel_entradas_historial", ok=1))

    # GET: mostrar formulario vacío (cargar lista de papeles)
    conn = get_conn()
    papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_entradas_nueva", modo="papel", papeles=papeles)


# ---------- PAPEL - HISTORIAL DE ENTRADAS ----------
@app.route("/papel/entradas/historial")
def papel_entradas_historial():
    conn = get_conn()
    registros = conn.execute("""
        SELECT fecha, tipo_papel, gramaje, formato, proveedor, marca, cantidad, observaciones
        FROM papel_entradas
        ORDER BY fecha DESC, id DESC
    """).fetchall()
    conn.close()
    return render_template(
        "base.html",
        vista="papel_entradas_historial",
        modo="papel",
        registros=registros
    )

# ---------- PAPEL - MENÚ SALIDAS ----------
@app.route("/papel/salidas")
def papel_salidas():
    return render_template(
        "base.html",
        vista="papel_salidas_menu",
        modo="papel"
    )


# ---------- PAPEL - REGISTRAR NUEVA SALIDA ----------
@app.route("/papel/salidas/nuevo", methods=["GET", "POST"])
def papel_salidas_nuevo():
    if request.method == "POST":
        tipo_papel    = request.form.get("tipo_papel", "").strip()
        gramaje       = request.form.get("gramaje", "").strip()
        formato       = request.form.get("formato", "").strip()
        proveedor     = request.form.get("proveedor", "").strip()
        marca         = request.form.get("marca", "").strip()
        cantidad      = request.form.get("cantidad", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        # Validación básica
        if (not tipo_papel or not gramaje or not formato or
                not proveedor or not marca or not cantidad):
            error = "Tenés que completar todos los campos obligatorios."
            # cargar lista de papeles para volver a mostrar el formulario
            conn = get_conn()
            papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
            conn.close()
            preview = {
                "tipo_papel": tipo_papel,
                "gramaje": gramaje,
                "formato": formato,
                "proveedor": proveedor,
                "marca": marca,
                "cantidad": cantidad,
                "observaciones": observaciones,
            }
            return render_template(
                "base.html",
                vista="papel_salidas_nueva",
                modo="papel",
                error=error,
                papeles=papeles,
                preview=preview,
            )

        # Guardar en la tabla de salidas de papel
        conn = get_conn()
        fecha = datetime.now().strftime("%Y-%m-%d")

        conn.execute("""
            INSERT INTO papel_salidas
                (fecha, tipo_papel, gramaje, formato,
                 proveedor, marca, cantidad, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha, tipo_papel, gramaje, formato,
            proveedor, marca, cantidad, observaciones
        ))

        conn.commit()
        conn.close()

        # Después de guardar, ir al historial de salidas de papel con ?ok=1
        return redirect(url_for("papel_salidas_historial", ok=1))

    # GET: mostrar formulario vacío (cargar lista de papeles)
    conn = get_conn()
    papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template(
        "base.html",
        vista="papel_salidas_nueva",
        modo="papel",
        papeles=papeles,
    )



# ---------- PAPEL - HISTORIAL DE SALIDAS ----------
@app.route("/papel/salidas/historial")
def papel_salidas_historial():
    conn = get_conn()
    registros = conn.execute("""
        SELECT fecha, tipo_papel, gramaje, formato, proveedor, marca, cantidad, observaciones
        FROM papel_salidas
        ORDER BY fecha DESC, id DESC
    """).fetchall()
    conn.close()

    return render_template(
        "base.html",
        vista="papel_salidas_historial",
        modo="papel",
        registros=registros
    )

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
# ...

# ---------- PAPEL - MENÚ PEDIDOS ----------
@app.route("/papel/pedidos")
def papel_pedidos():
    return render_template(
        "base.html",
        vista="papel_pedidos_menu",
        modo="papel"
    )


# ---------- PAPEL - REGISTRAR NUEVO PEDIDO ----------
@app.route("/papel/pedidos/nuevo", methods=["GET", "POST"])
def papel_pedidos_nuevo():
    if request.method == "POST":
        tipo_papel    = request.form.get("tipo_papel", "").strip()
        gramaje       = request.form.get("gramaje", "").strip()
        formato       = request.form.get("formato", "").strip()
        marca         = request.form.get("marca", "").strip()
        proveedor     = request.form.get("proveedor", "").strip()
        cantidad      = request.form.get("cantidad", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        # Validación básica
        if (not tipo_papel or not gramaje or not formato or
                not marca or not proveedor or not cantidad):
            error = "Tenés que completar todos los campos obligatorios."
            return render_template(
                "base.html",
                vista="papel_pedidos_nuevo",
                modo="papel",
                error=error
            )

        conn = get_conn()
        fecha = datetime.now().strftime("%Y-%m-%d")

        # Insertar en papel_pedidos
        conn.execute("""
            INSERT INTO papel_pedidos
                (fecha, tipo_papel, gramaje, formato,
                 marca, proveedor, cantidad, observaciones, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha, tipo_papel, gramaje, formato,
            marca, proveedor, cantidad, observaciones or None,
            "En espera"
        ))

        conn.commit()
        conn.close()

        # Después de guardar, ir al historial de pedidos de papel con ?ok=1
        return redirect(url_for("papel_pedidos_historial", ok=1))

    # GET: mostrar formulario de nuevo pedido de papel
    return render_template(
        "base.html",
        vista="papel_pedidos_nuevo",
        modo="papel"
    )


# ---------- PAPEL - HISTORIAL DE PEDIDOS ----------
@app.route("/papel/pedidos/historial")
def papel_pedidos_historial():
    conn = get_conn()
    registros = conn.execute("""
        SELECT * FROM papel_pedidos
        ORDER BY fecha DESC, id DESC
    """).fetchall()
    conn.close()

    return render_template(
        "base.html",
        vista="papel_pedidos_historial",
        modo="papel",
        registros=registros
    )


# ---------- PAPEL - MARCAR PEDIDO COMO ENTREGADO ----------
@app.route("/papel/pedidos/<int:pedido_id>/entregado", methods=["POST"])
def papel_pedido_entregado(pedido_id):
    conn = get_conn()
    pedido = conn.execute("""
        SELECT * FROM papel_pedidos WHERE id = ?
    """, (pedido_id,)).fetchone()

    if not pedido:
        conn.close()
        return jsonify({"ok": False, "error": "Pedido no encontrado"}), 404

    # Si ya estaba entregado, no hacemos nada
    if pedido["estado"] != "Entregado":
        # Marcamos como Entregado
        conn.execute("""
            UPDATE papel_pedidos
            SET estado = 'Entregado'
            WHERE id = ?
        """, (pedido_id,))

     
        conn.execute("""
            UPDATE papel_inventario
            SET stock_inicial = stock_inicial + ?,
                total         = total + ?
            WHERE nombre = ?
        """, (pedido["cantidad"], pedido["cantidad"], pedido["tipo_papel"]))

        conn.commit()

    conn.close()
    return jsonify({"ok": True})




if __name__ == "__main__":
    print("Levantando servidor Flask en http://127.0.0.1:5000/")
    app.run(debug=True)
