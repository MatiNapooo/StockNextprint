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
    "nicolas": "nnapoli",
    "luis": "nnapoli",
}


def credenciales_validas(usuario, contrasena):
    if not usuario or not contrasena:
        return False
    esperado = USUARIOS_ADMIN.get(usuario.strip())
    return esperado is not None and esperado == contrasena.strip()

from flask import Flask, render_template, request, redirect, url_for, session
# ...

app.secret_key = "cualquier_clave_larga_y_secreta"

# ---------- ADMIN (LOGIN + VISTA INVENTARIO INSUMOS) ----------
from flask import Flask, render_template, request, redirect, url_for, session
# (esto ya lo tenés, sólo confirmo que esté importado session)

# Clave para sesiones (si ya tenés una, dejá la tuya)
app.secret_key = "cualquier_clave_larga_y_secreta"


# --------- LOGIN ADMIN (INSUMOS) ----------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None

    # Si envían el formulario, validamos
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "").strip()

        cred_ok = (
            (usuario == "nnapoli" and contrasena == "matiesmihijofavorito") or
            (usuario == "luis" and contrasena == "nnapoli")
        )

        if cred_ok:
            session["admin_logueado"] = True
        else:
            error = "Usuario o contraseña incorrecta"

    # Si NO está logueado, mostramos login
    if not session.get("admin_logueado"):
        return render_template("base.html", vista="admin_login", modo="insumos", error=error)

    # Si está logueado, mostramos inventario de insumos (modo admin)
    conn = get_db_connection()
    registros = conn.execute("""
        SELECT * FROM inventario
        ORDER BY nombre
    """).fetchall()
    conn.close()

    return render_template(
        "base.html",
        vista="inventario_admin",   # bloque que va a mostrar la tabla con botones de admin
        modo="insumos",
        registros=registros
    )


# --------- LOGIN ADMIN PAPEL ----------
@app.route("/papel/admin", methods=["GET", "POST"])
def papel_admin():
    error = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "").strip()

        cred_ok = (
            (usuario == "nnapoli" and contrasena == "matiesmihijofavorito") or
            (usuario == "luis" and contrasena == "nnapoli")
        )

        if cred_ok:
            session["papel_admin_logueado"] = True
        else:
            error = "Usuario o contraseña incorrecta"

    if not session.get("papel_admin_logueado"):
        return render_template("base.html", vista="admin_login", modo="papel", error=error)

    # inventario SIMPLE de papel cuando está logueado
    conn = get_db_connection()
    registros = conn.execute("""
        SELECT * FROM papel_inventario
        ORDER BY tipo_papel
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
            session.permanent = True  # Sesión persiste hasta que haga logout explícito
            session["usuario_admin"] = usuario
            registros = obtener_registros_inventario()
            return render_template("base.html", vista="inventario", registros=registros)
        else:
            error = "Usuario o contraseña incorrecta"

    # GET inicial o POST fallido → mostrar formulario de login
    return render_template("base.html", vista="login_admin", login_error=error)

# ---------- PAPEL: INVENTARIO SIMPLE ----------
@app.route("/papel/inventario")
def papel_inventario():
    conn = get_db_connection()
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




# ---------------- ENTRADAS ----------------

@app.route("/entradas/nueva", methods=["GET", "POST"])
def entradas_nueva():
    # Usar la lista estándar de insumos (con nombre_mostrar y descripcion)
    insumos = obtener_insumos()

    if request.method == "POST":
        codigo = request.form.get("insumo_seleccionado", "").strip()
        cantidad_txt = request.form.get("unidad_seleccionada", "").strip()

        if codigo and cantidad_txt:
            try:
                cantidad = int(cantidad_txt)
                if cantidad > 0:
                    # Guardar en historial de entradas
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

                    conn = get_db_connection()
                    conn.execute("""
                        INSERT INTO entradas (fecha, insumo_codigo, cantidad)
                        VALUES (?, ?, ?)
                    """, (fecha_hoy, codigo, cantidad))

                    # Actualizar inventario: entradas y total
                    conn.execute("""
                        UPDATE inventario
                        SET entradas = entradas + ?,
                            total    = stock_inicial + entradas + ? - salidas
                        WHERE insumo_codigo = ?
                    """, (cantidad, cantidad, codigo))

                    conn.commit()
                    conn.close()

                    return redirect(url_for("entradas", ok=1))
            except ValueError:
                pass  # si hay error de número, simplemente no guarda

    registro_ok = request.args.get("ok") == "1"
    return render_template("base.html", vista="entradas_nueva", modo="insumos", insumos=insumos, registro_ok=registro_ok)


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
            conn = get_db_connection()
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

        conn = get_db_connection()
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
    conn = get_db_connection()
    insumos = conn.execute(
        "SELECT codigo, nombre, descripcion FROM insumos ORDER BY nombre"
    ).fetchall()
    conn.close()

    return render_template("base.html", vista="pedidos_nuevo", insumos=insumos)


@app.route("/pedidos/historial")
def pedidos_historial():
    conn = get_db_connection()
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

@app.route("/pedidos/<int:pedido_id>/entregar", methods=["POST"])
def pedido_entregado(pedido_id):
    conn = get_db_connection()
    pedido = conn.execute(
        "SELECT cantidad, insumo_codigo, estado FROM pedidos WHERE id = ?",
        (pedido_id,),
    ).fetchone()

    if pedido is None:
        conn.close()
        return redirect(url_for("pedidos_historial"))

    # Solo actualizamos si todavía no estaba entregado
    if pedido["estado"] != "Entregado":
        cantidad = pedido["cantidad"]
        insumo_codigo = pedido["insumo_codigo"]

        # Si el pedido está vinculado a un insumo del inventario
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

        # Marcar el pedido como entregado
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
            conn = get_db_connection()
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
        conn = get_db_connection()
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
    conn = get_db_connection()
    papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_entradas_nueva", modo="papel", papeles=papeles)


# ---------- PAPEL - HISTORIAL DE ENTRADAS ----------
@app.route("/papel/entradas/historial")
def papel_entradas_historial():
    conn = get_db_connection()
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
            conn = get_db_connection()
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
        conn = get_db_connection()
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
    conn = get_db_connection()
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
    conn = get_db_connection()
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

        conn = get_db_connection()
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
    conn = get_db_connection()
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
    conn = get_db_connection()
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

        # Actualizamos inventario de papel:
        # sumamos la cantidad a stock_inicial y total
        conn.execute("""
            UPDATE papel_inventario
            SET stock_inicial = stock_inicial + ?,
                total         = total + ?
            WHERE nombre = ?
        """, (pedido["cantidad"], pedido["cantidad"], pedido["tipo_papel"]))

        conn.commit()

    conn.close()
    return jsonify({"ok": True})



# ---------------- ARRANQUE APP ----------------

if __name__ == "__main__":
    print("Levantando servidor Flask en http://127.0.0.1:5000/")
    app.run(debug=True)
