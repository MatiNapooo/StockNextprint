import sqlite3
import os
import shutil 
from collections import Counter
from datetime import datetime
from sqlite3 import IntegrityError
from flask import Flask, render_template, request, redirect, url_for, session, jsonify


# --- BLOQUE MÁGICO PARA RAILWAY ---
def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Esta es la carpeta "segura" que crearemos en Railway
    railway_volumen = "/app/datos"
    
    # 1. ¿Estamos en Railway? (Si existe la carpeta del volumen)
    if os.path.exists(railway_volumen):
        db_path_volumen = os.path.join(railway_volumen, "stock.db")
        
        # 2. ¿El archivo ya está en el volumen?
        if not os.path.exists(db_path_volumen):
            # NO está (es la primera vez). Lo copiamos desde el código original.
            print("Iniciando carga de base de datos al volumen persistente...")
            origen = os.path.join(base_dir, "stock.db")
            if os.path.exists(origen):
                shutil.copy2(origen, db_path_volumen)
                print("¡Base de datos copiada con éxito!")
        
        return db_path_volumen
    else:
        # No estamos en Railway (estamos en tu PC)
        return os.path.join(base_dir, "stock.db")

# Usamos la función para definir la ruta
DB_PATH = get_db_path()

# ----------------------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH) # <-- Usamos la variable que calculamos arriba
    conn.row_factory = sqlite3.Row
    return conn

get_conn = get_db_connection

# ===== CONFIGURACIÓN FLASK =====
app = Flask(__name__)
app.secret_key = "nextprint-stock-super-secreto"

# ===== USUARIOS ADMIN =====
USUARIOS_ADMIN = {
    "nicolas": "nnapoli",
    "luis": "lonapoli",
}

# ===== PROTECCIÓN GLOBAL (LOGIN) =====
@app.before_request
def requerir_login():
    # Rutas exentas de login
    rutas_publicas = ['login', 'static']
    
    # Si la petición es a endpoint estático o login, dejamos pasar
    if request.endpoint == 'static' or request.endpoint == 'login':
        return

    # Si no tiene sesión autorizada, redirigir a login
    if not session.get("app_authorized"):
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "").strip()
        recordar = request.form.get("recordar") # Checkbox

        # Credenciales Globales
        if usuario == "nextprint" and contrasena == "npsa1141":
            session["app_authorized"] = True
            
            # Recordar sesión (hacerla permanente)
            if recordar:
                session.permanent = True
            else:
                session.permanent = False
                
            return redirect(url_for("menu_principal"))
        else:
            return render_template("base.html", vista="login_global", error="Credenciales inválidas")

    # Si ya está logueado, ir al menú
    if session.get("app_authorized"):
        return redirect(url_for("menu_principal"))

    return render_template("base.html", vista="login_global")

def credenciales_validas(usuario, contrasena):
    if not usuario or not contrasena:
        return False
    esperado = USUARIOS_ADMIN.get(usuario.strip())
    return esperado is not None and esperado == contrasena.strip()

# ===== INSUMOS =====
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

        return redirect(url_for("pedidos"))

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

        # Si el pedido está vinculado a un insumo del inventario, sumar al stock
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

# ==========================================
# SECCIÓN PAPEL (Agrega esto al final de app.py)
# ==========================================

# 1. ADMIN / INVENTARIO PAPEL
@app.route("/papel/admin", methods=["GET", "POST"])
def papel_admin():
    # Login simple separado para papel (opcional, o usa el mismo de insumos)
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "").strip()
        # Credenciales harcodeadas (puedes cambiarlas)
        if (usuario == "nicolas" and contrasena == "nnapoli") or \
           (usuario == "luis" and contrasena == "lonapoli"):
            session["papel_admin_logueado"] = True
        else:
            return render_template("base.html", vista="admin_login", modo="papel", error="Datos incorrectos")

    if not session.get("papel_admin_logueado"):
        return render_template("base.html", vista="admin_login", modo="papel")

    # Si está logueado, mostrar inventario admin
    conn = get_conn()
    registros = conn.execute("SELECT * FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_inventario_admin", modo="papel", registros=registros)

# ==========================================
# NUEVAS RUTAS PARA GESTIÓN DE PAPEL
# ==========================================

# 1. BORRAR MOVIMIENTO DE HISTORIAL (ENTRADA O SALIDA)
@app.route("/papel/historial/eliminar", methods=["POST"])
def papel_eliminar_movimiento():
    # Solo borra el registro del historial SIN modificar el inventario
    data = request.get_json() or {}
    mov_id = data.get("id")
    tipo = data.get("tipo") # "entrada" o "salida"

    if not mov_id or not tipo:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400

    conn = get_conn()
    try:
        # Tabla del historial
        tabla = "papel_entradas" if tipo == "entrada" else "papel_salidas"
        
        # Verificar que el registro existe
        registro = conn.execute(f"SELECT * FROM {tabla} WHERE id = ?", (mov_id,)).fetchone()
        if not registro:
            return jsonify({"ok": False, "error": "Registro no encontrado"}), 404

        # Eliminar SOLO el registro del historial, sin tocar el inventario
        conn.execute(f"DELETE FROM {tabla} WHERE id = ?", (mov_id,))
        conn.commit()
        
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
# ==========================================
# RUTAS DE GESTIÓN Y MODIFICACIÓN PAPEL (Solo una vez)
# ==========================================

# 1. BORRAR MOVIMIENTO DE HISTORIAL (ENTRADA O SALIDA)
@app.route("/papel/historial/eliminar", methods=["POST"])
def papel_eliminar_movimiento_historial():
    data = request.get_json() or {}
    mov_id = data.get("id")
    tipo = data.get("tipo") # "entrada" o "salida"

    if not mov_id or not tipo:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400

    conn = get_conn()
    try:
        # Buscar el registro para saber cantidad y tipo de papel
        tabla = "papel_entradas" if tipo == "entrada" else "papel_salidas"
        registro = conn.execute(f"SELECT * FROM {tabla} WHERE id = ?", (mov_id,)).fetchone()
        
        if not registro:
            return jsonify({"ok": False, "error": "Registro no encontrado"}), 404

        cantidad = registro["cantidad"]
        nombre_papel = registro["tipo_papel"] 

        # Eliminar el registro del historial
        conn.execute(f"DELETE FROM {tabla} WHERE id = ?", (mov_id,))

        # Actualizar el stock (INVERSO a la operación original)
        if tipo == "entrada":
            # Si borro una entrada, RESTO al stock
            conn.execute("""
                UPDATE papel_inventario 
                SET entradas = entradas - ?, total = total - ?
                WHERE nombre = ?
            """, (cantidad, cantidad, nombre_papel))
        else:
            # Si borro una salida, SUMO al stock (devuelvo el papel)
            conn.execute("""
                UPDATE papel_inventario 
                SET salidas = salidas - ?, total = total + ?
                WHERE nombre = ?
            """, (cantidad, cantidad, nombre_papel))

        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

# 2. MODIFICAR PAPEL (ADMIN) - Recalculando total
# IMPORTANTE: Asegúrate de que esta función aparezca solo una vez en todo el archivo
@app.route("/papel/modificar", methods=["POST"])
def papel_modificar():
    data = request.get_json(silent=True) or {}
    papel_id = data.get("id")
    nuevo_nombre = (data.get("nombre") or "").strip()
    
    # Datos numéricos
    stock_inicial = data.get("stock_inicial")
    entradas = data.get("entradas")
    salidas = data.get("salidas")

    if not papel_id:
        return jsonify({"ok": False, "error": "Falta ID"}), 400

    conn = get_conn()
    try:
        # Si vienen datos numéricos, recalculamos el total: (StockInicial + Entradas - Salidas)
        if stock_inicial is not None:
            total = int(stock_inicial) + int(entradas) - int(salidas)
            conn.execute("""
                UPDATE papel_inventario
                SET nombre = ?, stock_inicial = ?, entradas = ?, salidas = ?, total = ?
                WHERE id = ?
            """, (nuevo_nombre, stock_inicial, entradas, salidas, total, papel_id))
        else:
            # Solo cambio de nombre
            conn.execute("UPDATE papel_inventario SET nombre = ? WHERE id = ?", (nuevo_nombre, papel_id))
            
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"ok": False, "error": "Ya existe un papel con ese nombre"}), 400
    
    conn.close()
    return jsonify({"ok": True})
@app.route("/papel/inventario")
def papel_inventario():
    # Inventario modo lectura (para el menú principal)
    conn = get_conn()
    registros = conn.execute("SELECT * FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_inventario_simple", modo="papel", registros=registros)

# 2. ENTRADAS DE PAPEL
@app.route("/papel/entradas")
def papel_entradas():
    return render_template("base.html", vista="papel_entradas_menu", modo="papel")

@app.route("/papel/entradas/nuevo", methods=["GET", "POST"])
def papel_entradas_nuevo():
    conn = get_conn()
    if request.method == "POST":
        # Recibir los 7 datos específicos
        tipo_papel = request.form.get("tipo_papel", "").strip()
        gramaje = request.form.get("gramaje", "").strip()
        formato = request.form.get("formato", "").strip()
        marca = request.form.get("marca", "").strip()
        proveedor = request.form.get("proveedor", "").strip()
        cantidad = request.form.get("cantidad", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        fecha = datetime.now().strftime("%Y-%m-%d")

        # Guardar en historial entradas
        conn.execute("""
            INSERT INTO papel_entradas 
            (fecha, tipo_papel, gramaje, formato, marca, proveedor, cantidad, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha, tipo_papel, gramaje, formato, marca, proveedor, cantidad, observaciones))
        
        # Actualizar stock en inventario
        conn.execute("""
            UPDATE papel_inventario 
            SET entradas = entradas + ?, total = total + ? 
            WHERE nombre = ?
        """, (cantidad, cantidad, tipo_papel))
        
        conn.commit()
        conn.close()
        return redirect(url_for("papel_entradas_historial", ok=1))

    # GET: Cargar lista de papeles para el select
    papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_entradas_nueva", modo="papel", papeles=papeles)

@app.route("/papel/entradas/historial")
def papel_entradas_historial():
    conn = get_conn()
    registros = conn.execute("SELECT * FROM papel_entradas ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_entradas_historial", modo="papel", registros=registros)


# 3. SALIDAS DE PAPEL
@app.route("/papel/salidas")
def papel_salidas():
    return render_template("base.html", vista="papel_salidas_menu", modo="papel")

@app.route("/papel/salidas/nuevo", methods=["GET", "POST"])
def papel_salidas_nuevo():
    conn = get_conn()
    if request.method == "POST":
        tipo_papel = request.form.get("tipo_papel", "").strip()
        gramaje = request.form.get("gramaje", "").strip()
        formato = request.form.get("formato", "").strip()
        marca = request.form.get("marca", "").strip()
        proveedor = request.form.get("proveedor", "").strip()
        cantidad = request.form.get("cantidad", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        fecha = datetime.now().strftime("%Y-%m-%d")

        # Guardar en historial salidas
        conn.execute("""
            INSERT INTO papel_salidas 
            (fecha, tipo_papel, gramaje, formato, marca, proveedor, cantidad, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha, tipo_papel, gramaje, formato, marca, proveedor, cantidad, observaciones))

        # Restar stock en inventario
        conn.execute("""
            UPDATE papel_inventario 
            SET salidas = salidas + ?, total = total - ? 
            WHERE nombre = ?
        """, (cantidad, cantidad, tipo_papel))

        conn.commit()
        conn.close()
        return redirect(url_for("papel_salidas_historial", ok=1))

    papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_salidas_nueva", modo="papel", papeles=papeles)

@app.route("/papel/salidas/historial")
def papel_salidas_historial():
    conn = get_conn()
    registros = conn.execute("SELECT * FROM papel_salidas ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_salidas_historial", modo="papel", registros=registros)


@app.route("/papel/entradas/<int:id>/borrar", methods=["POST"])
def papel_borrar_entrada(id):
    conn = get_conn()
    # Borrado simple (igual que insumos), no toca el stock
    conn.execute("DELETE FROM papel_entradas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return ("", 204)

@app.route("/papel/salidas/<int:id>/borrar", methods=["POST"])
def papel_borrar_salida(id):
    conn = get_conn()
    # Borrado simple (igual que insumos), no toca el stock
    conn.execute("DELETE FROM papel_salidas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return ("", 204)

# 4. PEDIDOS DE PAPEL
@app.route("/papel/pedidos")
def papel_pedidos():
    return render_template("base.html", vista="papel_pedidos_menu", modo="papel")

@app.route("/papel/pedidos/nuevo", methods=["GET", "POST"])
def papel_pedidos_nuevo():
    conn = get_conn()
    if request.method == "POST":
        # AGREGADO: Obtener 'pedido_por'
        pedido_por = request.form.get("pedido_por", "").strip()
        
        tipo_papel = request.form.get("tipo_papel", "").strip()
        gramaje = request.form.get("gramaje", "").strip()
        formato = request.form.get("formato", "").strip()
        marca = request.form.get("marca", "").strip()
        proveedor = request.form.get("proveedor", "").strip()
        cantidad = request.form.get("cantidad", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        fecha = datetime.now().strftime("%Y-%m-%d")

        # AGREGADO: Incluir 'pedido_por' en el INSERT
        # Nota: Asegúrate de que tu tabla 'papel_pedidos' tenga la columna 'pedido_por'.
        # Si no la tiene, tendrás que agregarla manualmente a la base de datos o el código dará error.
        conn.execute("""
            INSERT INTO papel_pedidos 
            (fecha, pedido_por, tipo_papel, gramaje, formato, marca, proveedor, cantidad, observaciones, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'En espera')
        """, (fecha, pedido_por, tipo_papel, gramaje, formato, marca, proveedor, cantidad, observaciones))

        conn.commit()
        conn.close()
        return redirect(url_for("papel_pedidos_historial", ok=1))

    papeles = conn.execute("SELECT nombre FROM papel_inventario ORDER BY nombre").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_pedidos_nuevo", modo="papel", papeles=papeles)

@app.route("/papel/pedidos/historial")
def papel_pedidos_historial():
    conn = get_conn()
    registros = conn.execute("SELECT * FROM papel_pedidos ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("base.html", vista="papel_pedidos_historial", modo="papel", registros=registros)

@app.route("/papel/pedidos/<int:pedido_id>/entregado", methods=["POST"])
def papel_pedido_entregado(pedido_id):
    conn = get_conn()
    # Verificar pedido
    pedido = conn.execute("SELECT * FROM papel_pedidos WHERE id = ?", (pedido_id,)).fetchone()
    
    if pedido and pedido["estado"] != "Entregado":
        # Marcar entregado
        conn.execute("UPDATE papel_pedidos SET estado = 'Entregado' WHERE id = ?", (pedido_id,))
        # Sumar al stock automáticamente cuando se entrega
        conn.execute("""
            UPDATE papel_inventario 
            SET stock_inicial = stock_inicial + ?, total = total + ? 
            WHERE nombre = ?
        """, (pedido["cantidad"], pedido["cantidad"], pedido["tipo_papel"]))
        conn.commit()
        
    conn.close()
    return jsonify({"ok": True})
    return jsonify({"ok": True})

# ==========================================
# GESTIÓN DE INVENTARIO PAPEL (Agregar al final de app.py)
# ==========================================

# 1. AGREGAR NUEVO PAPEL
@app.route("/papel/agregar", methods=["POST"])
def papel_agregar():
    if not session.get("papel_admin_logueado"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    stock = int(data.get("stock") or 0)

    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400

    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO papel_inventario (nombre, stock_inicial, entradas, salidas, total)
            VALUES (?, ?, 0, 0, ?)
        """, (nombre, stock, stock))
        conn.commit()
        # Recuperar ID generado
        row = conn.execute("SELECT id FROM papel_inventario WHERE nombre = ?", (nombre,)).fetchone()
        new_id = row["id"]
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"ok": False, "error": "Ya existe un papel con ese nombre"}), 400
    
    conn.close()
    return jsonify({"ok": True, "id": new_id, "nombre": nombre, "stock": stock, "total": stock})

# 2. ELIMINAR PAPEL
@app.route("/papel/eliminar", methods=["POST"])
def papel_eliminar():
    if not session.get("papel_admin_logueado"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json(silent=True) or {}
    papel_id = data.get("id")

    if not papel_id:
        return jsonify({"ok": False, "error": "Falta ID del papel"}), 400

    conn = get_conn()
    # Obtenemos nombre para borrar historial si quisieras (opcional)
    # row = conn.execute("SELECT nombre FROM papel_inventario WHERE id = ?", (papel_id,)).fetchone()
    
    conn.execute("DELETE FROM papel_inventario WHERE id = ?", (papel_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})



# ---------------- ARRANQUE APP ----------------

if __name__ == "__main__":
    print("Levantando servidor Flask en http://127.0.0.1:5000/")
    app.run(debug=True)
