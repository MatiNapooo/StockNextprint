document.addEventListener("DOMContentLoaded", function () {
    // -------------------
    // REGISTRO (entradas / salidas)
    // -------------------
    const confirmButton = document.querySelector(".confirm-button");
    const previewSection = document.getElementById("preview-section");
    const previewWrapper = document.getElementById("preview-table-wrapper");
    const insumoSelect = document.getElementById("insumo_seleccionado");
    const unidadSelect = document.getElementById("unidad_seleccionada");

    const errorInsumo = document.getElementById("error-insumo");
    const errorUnidad = document.getElementById("error-unidad");

    const insumoImg = document.getElementById("insumo-imagen");
    const imgBase = insumoSelect ? insumoSelect.dataset.imgBase : "";

    if (
        confirmButton &&
        previewSection &&
        previewWrapper &&
        insumoSelect &&
        unidadSelect &&
        errorInsumo &&
        errorUnidad
    ) {
        // Actualizar imagen del insumo al cambiar el select
        function actualizarImagenInsumo() {
            if (!insumoImg || !imgBase) return;

            const codigo = insumoSelect.value;
            if (!codigo) {
                insumoImg.style.display = "none";
                insumoImg.removeAttribute("src");
                return;
            }

            insumoImg.style.display = "block";
            insumoImg.src = imgBase + codigo + ".png";
            insumoImg.onerror = function () {
                insumoImg.style.display = "none";
            };
        }

        if (insumoImg) {
            insumoSelect.addEventListener("change", actualizarImagenInsumo);
        }

        // Confirmar → validar + generar vista previa (NO guarda)
        confirmButton.addEventListener("click", function () {
            // Limpiar errores
            errorInsumo.textContent = "";
            errorUnidad.textContent = "";

            let hayError = false;

            if (!insumoSelect.value) {
                errorInsumo.textContent = "*Tenes que rellenar esta casilla";
                hayError = true;
            }

            if (!unidadSelect.value) {
                errorUnidad.textContent = "*Tenes que rellenar esta casilla";
                hayError = true;
            }

            if (hayError) {
                previewSection.style.display = "none";
                previewWrapper.innerHTML = "";
                return;
            }

            const selectedOption = insumoSelect.options[insumoSelect.selectedIndex];

            const codigo = selectedOption.value || "";
            const nombre = selectedOption.dataset.nombre || "";
            const descripcion = selectedOption.dataset.descripcion || "";
            const cantidad = unidadSelect.value || "";

            const hoy = new Date();
            const fecha = hoy.toLocaleDateString("es-AR", {
                day: "numeric",
                month: "short",
            });

            const tablaHTML = `
                <table class="preview-table">
                    <thead>
                        <tr>
                            <th>FECHA</th>
                            <th>CÓDIGO</th>
                            <th>INSUMO</th>
                            <th>DESCRIPCIÓN</th>
                            <th>CANTIDAD</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>${fecha}</td>
                            <td>${codigo}</td>
                            <td>${nombre}</td>
                            <td>${descripcion}</td>
                            <td>${cantidad}</td>
                        </tr>
                    </tbody>
                </table>
            `;

            previewWrapper.innerHTML = tablaHTML;
            previewSection.style.display = "flex";
        });
    }

    // -------------------
    // HISTORIAL: filtro + modal BORRAR
    // -------------------
    const filtroInput = document.getElementById("filtro-historial");
    const tablaHistorial = document.getElementById("tabla-historial");

    const modalBorrar = document.getElementById("modal-borrar");
    const modalBtnSi = modalBorrar ? modalBorrar.querySelector(".modal-btn-si") : null;
    const modalBtnNo = modalBorrar ? modalBorrar.querySelector(".modal-btn-no") : null;

    let borrarPendiente = { id: null, tipo: null, fila: null };

    if (filtroInput && tablaHistorial) {
        // Filtro tipo Excel
        filtroInput.addEventListener("input", function () {
            const filtro = filtroInput.value.trim().toLowerCase();
            const filas = tablaHistorial.querySelectorAll("tbody tr");

            filas.forEach((tr) => {
                const textoFila = tr.textContent.toLowerCase();

                if (!filtro) {
                    // sin filtro -> mostrar todo
                    tr.style.display = "";
                } else if (textoFila.includes(filtro)) {
                    tr.style.display = "";
                } else {
                    tr.style.display = "none";
                }
            });
        });

        // Click en BORRAR → abrir modal
        tablaHistorial.addEventListener("click", function (e) {
            const btn = e.target.closest(".btn-borrar");
            if (!btn) return;

            const id = btn.dataset.id;
            const tipo = btn.dataset.tipo; // "entrada" o "salida"
            const fila = btn.closest("tr");

            borrarPendiente = { id, tipo, fila };

            if (modalBorrar) {
                modalBorrar.style.display = "flex";
            }
        });
    }

    if (modalBorrar && modalBtnSi && modalBtnNo) {
        // NO → cerrar modal
        modalBtnNo.addEventListener("click", function () {
            modalBorrar.style.display = "none";
            borrarPendiente = { id: null, tipo: null, fila: null };
        });

        // SI → borrar en servidor y quitar fila
        modalBtnSi.addEventListener("click", function () {
            if (!borrarPendiente.id || !borrarPendiente.tipo) {
                modalBorrar.style.display = "none";
                return;
            }

            const url =
                borrarPendiente.tipo === "entrada"
                    ? `/entradas/${borrarPendiente.id}/borrar`
                    : `/salidas/${borrarPendiente.id}/borrar`;

            fetch(url, { method: "POST" })
                .then((resp) => {
                    if (resp.ok) {
                        if (borrarPendiente.fila) {
                            borrarPendiente.fila.remove();
                        }
                    } else {
                        alert("No se pudo borrar el registro.");
                    }
                })
                .catch(() => {
                    alert("Error al comunicarse con el servidor.");
                })
                .finally(() => {
                    modalBorrar.style.display = "none";
                    borrarPendiente = { id: null, tipo: null, fila: null };
                });
        });
    }

       // -------------------
    // INVENTARIO: filtro
    // -------------------
    const tablaInventario = document.getElementById("tabla-inventario");
    const filtroInv = document.getElementById("filtro-inventario");

    if (tablaInventario && filtroInv) {
        filtroInv.addEventListener("input", function () {
            const filtro = filtroInv.value.trim().toLowerCase();
            const filas = tablaInventario.querySelectorAll("tbody tr");

            filas.forEach((tr) => {
                const texto = tr.textContent.toLowerCase();
                if (!filtro || texto.includes(filtro)) {
                    tr.style.display = "";
                } else {
                    tr.style.display = "none";
                }
            });
        });
    }

         // -------------------
        // INVENTARIO SIMPLE (solo lectura): filtro
        // -------------------
        const tablaInventarioSimple = document.getElementById("tabla-inventario-simple");
        const filtroInvSimple = document.getElementById("filtro-inventario-simple");

        if (tablaInventarioSimple && filtroInvSimple) {
            filtroInvSimple.addEventListener("input", function () {
                const filtro = filtroInvSimple.value.trim().toLowerCase();
                const filas = tablaInventarioSimple.querySelectorAll("tbody tr");

                filas.forEach((tr) => {
                    const texto = tr.textContent.toLowerCase();
                    if (!filtro || texto.includes(filtro)) {
                        tr.style.display = "";
                    } else {
                        tr.style.display = "none";
                    }
                });
            });
    }


    // -------------------
    // INVENTARIO: popup MODIFICAR cantidades
    // -------------------
    const modalInv = document.getElementById("modal-inventario");
    const invCerrar = document.getElementById("inv-modal-cerrar");
    const invConfirmar = document.getElementById("inv-modal-confirmar");
    const inputStock = document.getElementById("inv-stock");
    const inputEntradas = document.getElementById("inv-entradas");
    const inputSalidas = document.getElementById("inv-salidas");
    const inputTotal = document.getElementById("inv-total");

    let inventarioFilaActual = null;
    let inventarioIdActual = null;

    if (tablaInventario && modalInv && invCerrar && invConfirmar) {
        tablaInventario.addEventListener("click", function (e) {
            const btn = e.target.closest(".btn-modificar");
            if (!btn) return;

            inventarioIdActual = btn.dataset.id;
            inventarioFilaActual = btn.closest("tr");

            inputStock.value = btn.dataset.stock || "0";
            inputEntradas.value = btn.dataset.entradas || "0";
            inputSalidas.value = btn.dataset.salidas || "0";
            inputTotal.value = btn.dataset.total || "0";

            modalInv.style.display = "flex";
        });

        invCerrar.addEventListener("click", function () {
            modalInv.style.display = "none";
            inventarioFilaActual = null;
            inventarioIdActual = null;
        });

        invConfirmar.addEventListener("click", function () {
            if (!inventarioIdActual || !inventarioFilaActual) {
                modalInv.style.display = "none";
                return;
            }

            const payload = {
                stock_inicial: parseInt(inputStock.value || "0", 10),
                entradas: parseInt(inputEntradas.value || "0", 10),
                salidas: parseInt(inputSalidas.value || "0", 10),
            };

            fetch(`/inventario/${inventarioIdActual}/actualizar`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then((resp) => resp.json())
                .then((data) => {
                    if (!data.ok) throw new Error("Error al actualizar inventario");

                    const celdas = inventarioFilaActual.querySelectorAll("td");
                    celdas[3].textContent = data.stock_inicial;
                    celdas[4].textContent = data.entradas;
                    celdas[5].textContent = data.salidas;
                    celdas[6].textContent = data.total;

                    const btn = inventarioFilaActual.querySelector(".btn-modificar");
                    if (btn) {
                        btn.dataset.stock = data.stock_inicial;
                        btn.dataset.entradas = data.entradas;
                        btn.dataset.salidas = data.salidas;
                        btn.dataset.total = data.total;
                    }

                    modalInv.style.display = "none";
                    inventarioFilaActual = null;
                    inventarioIdActual = null;
                })
                .catch((err) => {
                    console.error(err);
                    alert("No se pudo actualizar el inventario.");
                    modalInv.style.display = "none";
                });
        });
    }
    // -------------------
    // INVENTARIO: ELIMINAR INSUMO
    // -------------------
    const delSelect = document.getElementById("del-insumo-select");
    const delEliminar = document.getElementById("del-insumo-eliminar");
    const modalDelConfirm = document.getElementById("modal-insumo-confirm");
    const delConfSi = document.getElementById("insumo-conf-si");
    const delConfNo = document.getElementById("insumo-conf-no");

    let codigoAEliminar = null;

    document.addEventListener("DOMContentLoaded", function () {

            // Funciones globales para abrir/cerrar el modal de ELIMINAR INSUMO
   
    });

    if (
        tablaInventario &&
        delSelect &&
        delEliminar &&
        modalDelConfirm &&
        delConfSi &&
        delConfNo
    ) {
        // Click en "Eliminar" dentro del primer popup
        delEliminar.addEventListener("click", function () {
            const codigo = delSelect.value;
            if (!codigo) {
                alert("Seleccione un insumo.");
                return;
            }
            codigoAEliminar = codigo;
            modalDelConfirm.style.display = "flex";
        });

        // Click en "NO" en el popup de confirmación
        delConfNo.addEventListener("click", function () {
            modalDelConfirm.style.display = "none";
            codigoAEliminar = null;
        });

        // Click en "SI" en el popup de confirmación
        delConfSi.addEventListener("click", function () {
            if (!codigoAEliminar) {
                modalDelConfirm.style.display = "none";
                return;
            }

            fetch(`/insumos/${codigoAEliminar}/eliminar`, {
                method: "POST",
            })
                .then((resp) => resp.json())
                .then((data) => {
                    if (!data.ok) throw new Error("No se pudo eliminar insumo");

                    // ... (borrado de fila y opciones)

                    modalDelConfirm.style.display = "none";
                    const modalEliminar = document.getElementById("modal-insumo-eliminar");
                    if (modalEliminar) modalEliminar.style.display = "none";
                    document.body.classList.remove("modal-eliminar-open");
                    codigoAEliminar = null;
                })

                .catch((err) => {
                    console.error(err);
                    alert("Error al eliminar insumo.");
                    modalDelConfirm.style.display = "none";
                });
        });
    }

    // -------------------
    // INVENTARIO: MODIFICAR INSUMO (datos del insumo)
    // -------------------
    const btnEditarInsumo = document.querySelector(".btn-editar-insumo");
    const modalEditInsumo = document.getElementById("modal-insumo-editar");
    const editCerrar = document.getElementById("edit-insumo-cerrar");
    const editConfirmar = document.getElementById("edit-insumo-confirmar");

    const editSelectInsumo = document.getElementById("edit-insumo-select");
    const editCodigo = document.getElementById("edit-codigo");
    const editNombre = document.getElementById("edit-nombre");
    const editDescripcion = document.getElementById("edit-descripcion");
    const editUnidad = document.getElementById("edit-unidad");

    function cargarDatosEdicion() {
        const opt = editSelectInsumo.options[editSelectInsumo.selectedIndex];
        if (!opt) return;
        editCodigo.value = opt.value;
        editNombre.value = opt.dataset.nombre || "";
        editDescripcion.value = opt.dataset.descripcion || "";
        editUnidad.value = opt.dataset.unidad || "";
    }

    if (
        tablaInventario &&
        btnEditarInsumo &&
        modalEditInsumo &&
        editCerrar &&
        editConfirmar &&
        editSelectInsumo
    ) {
        btnEditarInsumo.addEventListener("click", function () {
            cargarDatosEdicion();
            modalEditInsumo.style.display = "flex";
        });

        editSelectInsumo.addEventListener("change", cargarDatosEdicion);

        editCerrar.addEventListener("click", function () {
            modalEditInsumo.style.display = "none";
        });

        editConfirmar.addEventListener("click", function () {
            const codigoOriginal = editSelectInsumo.value;

            const payload = {
                codigo_original: codigoOriginal,
                codigo_nuevo: editCodigo.value.trim(),
                nombre: editNombre.value.trim(),
                descripcion: editDescripcion.value.trim(),
                unidad: editUnidad.value.trim(),
            };

            if (!payload.codigo_nuevo || !payload.nombre) {
                alert("Código e insumo son obligatorios.");
                return;
            }

            fetch("/insumos/modificar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then((resp) => resp.json().then((data) => ({ ok: resp.ok, data })))
                .then(({ ok, data }) => {
                    if (!ok || !data.ok) {
                        alert(data.error || "No se pudo modificar el insumo.");
                        return;
                    }

                    // actualizar option del selector de edición
                    const opt = editSelectInsumo.options[editSelectInsumo.selectedIndex];
                    opt.value = data.codigo;
                    opt.dataset.nombre = data.nombre;
                    opt.dataset.descripcion = data.descripcion || "";
                    opt.dataset.unidad = data.unidad || "";
                    opt.textContent =
                        data.codigo +
                        " - " +
                        data.nombre +
                        " " +
                        (data.descripcion || "");

                    // actualizar option en selector de eliminar
                    if (delSelect) {
                        [...delSelect.options].forEach((o) => {
                            if (o.value === codigoOriginal) {
                                o.value = data.codigo;
                                o.textContent =
                                    data.codigo +
                                    " - " +
                                    data.nombre +
                                    " " +
                                    (data.descripcion || "");
                            }
                        });
                    }

                    // actualizar fila en tabla inventario
                    const fila = tablaInventario.querySelector(
                        `tr[data-codigo="${codigoOriginal}"]`
                    );
                    if (fila) {
                        fila.dataset.codigo = data.codigo;
                        const celdas = fila.querySelectorAll("td");
                        celdas[0].textContent = data.codigo;
                        celdas[1].textContent = data.nombre;
                        celdas[2].textContent = data.descripcion || "";
                    }

                    modalEditInsumo.style.display = "none";
                })
                .catch((err) => {
                    console.error(err);
                    alert("Error al comunicarse con el servidor.");
                });
        });
    }

    // -------------------
    // INVENTARIO: popup AGREGAR INSUMO
    // -------------------
    const btnAgregarInsumo = document.querySelector(".btn-agregar-insumo");
    const modalInsumo = document.getElementById("modal-insumo");
    const insCerrar = document.getElementById("insumo-modal-cerrar");
    const insConfirmar = document.getElementById("insumo-modal-confirmar");

    const insCodigo = document.getElementById("ins-codigo");
    const insNombre = document.getElementById("ins-nombre");
    const insDescripcion = document.getElementById("ins-descripcion");
    const insUnidad = document.getElementById("ins-unidad");
    const insStock = document.getElementById("ins-stock");

    if (
        tablaInventario &&
        btnAgregarInsumo &&
        modalInsumo &&
        insCerrar &&
        insConfirmar
    ) {
        btnAgregarInsumo.addEventListener("click", function () {
            insCodigo.value = "";
            insNombre.value = "";
            insDescripcion.value = "";
            insUnidad.value = "";
            insStock.value = "0";

            modalInsumo.style.display = "flex";
        });

        insCerrar.addEventListener("click", function () {
            modalInsumo.style.display = "none";
        });

        insConfirmar.addEventListener("click", function () {
            const payload = {
                codigo: insCodigo.value.trim(),
                nombre: insNombre.value.trim(),
                descripcion: insDescripcion.value.trim(),
                unidad: insUnidad.value.trim(),
                stock_inicial: parseInt(insStock.value || "0", 10),
            };

            if (!payload.codigo || !payload.nombre) {
                alert("Código e insumo son obligatorios.");
                return;
            }

            fetch("/insumos/nuevo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then((resp) => resp.json().then((data) => ({ ok: resp.ok, data })))
                .then(({ ok, data }) => {
                    if (!ok || !data.ok) {
                        alert(data.error || "No se pudo agregar el insumo.");
                        return;
                    }

                    const tbody = tablaInventario.querySelector("tbody");
                    const tr = document.createElement("tr");
                    tr.setAttribute("data-item-id", data.inventario_id);
                    tr.setAttribute("data-codigo", data.codigo);

                    tr.innerHTML = `
                        <td>${data.codigo}</td>
                        <td>${data.nombre}</td>
                        <td>${data.descripcion || ""}</td>
                        <td>${data.stock_inicial}</td>
                        <td>${data.entradas}</td>
                        <td>${data.salidas}</td>
                        <td>${data.total}</td>
                        <td>
                            <button type="button"
                                    class="btn-modificar"
                                    data-id="${data.inventario_id}"
                                    data-stock="${data.stock_inicial}"
                                    data-entradas="${data.entradas}"
                                    data-salidas="${data.salidas}"
                                    data-total="${data.total}">
                                Modificar
                            </button>
                        </td>
                    `;

                    tbody.appendChild(tr);
                    modalInsumo.style.display = "none";
                })
                .catch((err) => {
                    console.error(err);
                    alert("Error al comunicarse con el servidor.");
                });
        });
    }

    // -------------------
    // MODAL "¡Registro confirmado!"
    // -------------------
    const modalOk = document.getElementById("modal-ok");
    if (modalOk && modalOk.dataset.activo === "1") {
        // Mostrar el modal
        modalOk.style.display = "flex";

        setTimeout(function () {
            modalOk.style.display = "none";

            // Limpiar ?ok=1 de la URL
            if (window.location.search.includes("ok=1")) {
                const nuevaUrl = window.location.pathname;
                window.history.replaceState(null, "", nuevaUrl);
            }

            // Limpiar vista previa
            if (previewSection && previewWrapper) {
                previewSection.style.display = "none";
                previewWrapper.innerHTML = "";
            }

            // Resetear selects
            if (insumoSelect) insumoSelect.selectedIndex = 0;
            if (unidadSelect) unidadSelect.selectedIndex = 0;

            // Ocultar imagen de insumo
            if (insumoImg) {
                insumoImg.style.display = "none";
                insumoImg.removeAttribute("src");
            }
        }, 3000);
    }
});
