document.addEventListener("DOMContentLoaded", function () {
    // ===== REGISTRO ENTRADAS/SALIDAS =====
    const insumoSelect = document.getElementById("insumo_seleccionado");
    const unidadSelect = document.getElementById("unidad_seleccionada");
    const errorInsumo = document.getElementById("error-insumo");
    const errorUnidad = document.getElementById("error-unidad");
    const insumoImg = document.getElementById("insumo-imagen");
    const imgBase = insumoSelect ? insumoSelect.dataset.imgBase : "";

    const formEntrada = document.getElementById("form-entrada-nueva");
    const formSalida = document.getElementById("form-salida-nueva");
    const esEntrada = formEntrada !== null;
    const esSalida = formSalida !== null;

    if (insumoSelect && unidadSelect && errorInsumo && errorUnidad) {
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

        let confirmButton = null;
        let modalPrevia = null;
        let btnCancelar = null;

        if (esEntrada) {
            confirmButton = document.getElementById("btn-entrada-confirmar");
            modalPrevia = document.getElementById("modal-entrada-previa");
            btnCancelar = document.getElementById("entrada-previa-cancelar");
        } else if (esSalida) {
            confirmButton = document.getElementById("btn-salida-confirmar");
            modalPrevia = document.getElementById("modal-salida-previa");
            btnCancelar = document.getElementById("salida-previa-cancelar");
        }

        if (confirmButton && modalPrevia && btnCancelar) {
            confirmButton.addEventListener("click", function () {
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
                if (hayError) return;

                const selectedOption = insumoSelect.options[insumoSelect.selectedIndex];
                const codigo = selectedOption.value || "";
                const nombre = selectedOption.dataset.nombre || "";
                const descripcion = selectedOption.dataset.descripcion || "";
                const cantidad = unidadSelect.value || "";
                const hoy = new Date();
                const fecha = hoy.toLocaleDateString("es-AR");

                if (esEntrada) {
                    document.getElementById("prev-entrada-fecha").textContent = fecha;
                    document.getElementById("prev-entrada-codigo").textContent = codigo;
                    document.getElementById("prev-entrada-insumo").textContent = nombre;
                    document.getElementById("prev-entrada-descripcion").textContent = descripcion;
                    document.getElementById("prev-entrada-cantidad").textContent = cantidad;
                } else if (esSalida) {
                    document.getElementById("prev-salida-fecha").textContent = fecha;
                    document.getElementById("prev-salida-codigo").textContent = codigo;
                    document.getElementById("prev-salida-insumo").textContent = nombre;
                    document.getElementById("prev-salida-descripcion").textContent = descripcion;
                    document.getElementById("prev-salida-cantidad").textContent = cantidad;
                }
                modalPrevia.style.display = "flex";
            });

            btnCancelar.addEventListener("click", function () {
                modalPrevia.style.display = "none";
            });
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        // ===== INVENTARIO FILTROS =====
        const tablaInventario = document.getElementById("tabla-inventario");
        const filtroInv = document.getElementById("filtro-inventario");
        if (tablaInventario && filtroInv) {
            filtroInv.addEventListener("input", function () {
                const filtro = filtroInv.value.trim().toLowerCase();
                const filas = tablaInventario.querySelectorAll("tbody tr");
                filas.forEach((tr) => {
                    const texto = tr.textContent.toLowerCase();
                    tr.style.display = (!filtro || texto.includes(filtro)) ? "" : "none";
                });
            });
        }

        const tablaInventarioSimple = document.getElementById("tabla-inventario-simple");
        const filtroInvSimple = document.getElementById("filtro-inventario-simple");
        if (tablaInventarioSimple && filtroInvSimple) {
            filtroInvSimple.addEventListener("input", function () {
                const filtro = filtroInvSimple.value.trim().toLowerCase();
                const filas = tablaInventarioSimple.querySelectorAll("tbody tr");
                filas.forEach((tr) => {
                    const texto = tr.textContent.toLowerCase();
                    tr.style.display = (!filtro || texto.includes(filtro)) ? "" : "none";
                });
            });
        }

        // ===== INVENTARIO MODIFICAR CANTIDADES =====
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
            });

            invConfirmar.addEventListener("click", function () {
                if (!inventarioIdActual) return;
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
                    .then(r => r.json())
                    .then(data => {
                        if (!data.ok) throw new Error("Error");
                        const celdas = inventarioFilaActual.querySelectorAll("td");
                        celdas[3].textContent = data.stock_inicial;
                        celdas[4].textContent = data.entradas;
                        celdas[5].textContent = data.salidas;
                        celdas[6].textContent = data.total;
                        const btn = inventarioFilaActual.querySelector(".btn-modificar");
                        btn.dataset.stock = data.stock_inicial;
                        btn.dataset.entradas = data.entradas;
                        btn.dataset.salidas = data.salidas;
                        btn.dataset.total = data.total;
                        modalInv.style.display = "none";
                    })
                    .catch(e => alert("No se pudo actualizar."));
            });
        }

        // ===== INVENTARIO ELIMINAR INSUMO =====
        const delSelect = document.getElementById("del-insumo-select");
        const delEliminar = document.getElementById("del-insumo-eliminar");
        const modalDelConfirm = document.getElementById("modal-insumo-confirm");
        const delConfSi = document.getElementById("insumo-conf-si");
        const delConfNo = document.getElementById("insumo-conf-no");
        let codigoAEliminar = null;

        if (delEliminar && modalDelConfirm) {
            delEliminar.addEventListener("click", function () {
                const codigo = delSelect.value;
                if (!codigo) {
                    alert("Seleccione un insumo.");
                    return;
                }
                codigoAEliminar = codigo;
                modalDelConfirm.style.display = "flex";
            });

            delConfNo.addEventListener("click", function () {
                modalDelConfirm.style.display = "none";
                codigoAEliminar = null;
            });

            delConfSi.addEventListener("click", function () {
                if (!codigoAEliminar) return;
                fetch(`/insumos/${codigoAEliminar}/eliminar`, { method: "POST" })
                    .then(r => r.json())
                    .then(data => {
                        if (!data.ok) throw new Error("Error");
                        location.reload();
                    })
                    .catch(() => alert("Error al eliminar."));
            });
        }

        // ===== INVENTARIO MODIFICAR DATOS INSUMO =====
        const modalEditInsumo = document.getElementById("modal-insumo-editar");
        const editCerrar = document.getElementById("edit-insumo-cerrar");
        const editConfirmar = document.getElementById("edit-insumo-confirmar");
        const editSelectInsumo = document.getElementById("edit-insumo-select");

        if (modalEditInsumo && editSelectInsumo) {
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

            editSelectInsumo.addEventListener("change", cargarDatosEdicion);

            if (editCerrar) {
                editCerrar.addEventListener("click", () => modalEditInsumo.style.display = "none");
            }

            if (editConfirmar) {
                editConfirmar.addEventListener("click", function () {
                    const payload = {
                        codigo_original: editSelectInsumo.value,
                        codigo_nuevo: editCodigo.value.trim(),
                        nombre: editNombre.value.trim(),
                        descripcion: editDescripcion.value.trim(),
                        unidad: editUnidad.value.trim(),
                    };
                    if (!payload.codigo_nuevo || !payload.nombre) return alert("Faltan datos");

                    fetch("/insumos/modificar", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    })
                        .then(r => r.json())
                        .then(data => {
                            if (!data.ok) throw new Error(data.error);
                            location.reload();
                        })
                        .catch(e => alert(e.message));
                });
            }
        }

        // ===== INVENTARIO AGREGAR INSUMO =====
        const modalInsumo = document.getElementById("modal-insumo");
        const insCerrar = document.getElementById("insumo-modal-cerrar");
        const insConfirmar = document.getElementById("insumo-modal-confirmar");

        const insCodigo = document.getElementById("ins-codigo");
        const insNombre = document.getElementById("ins-nombre");
        const insDescripcion = document.getElementById("ins-descripcion");
        const insUnidad = document.getElementById("ins-unidad");
        const insStock = document.getElementById("ins-stock");

        if (modalInsumo && insConfirmar) {
            if (insCerrar) {
                insCerrar.addEventListener("click", () => modalInsumo.style.display = "none");
            }

            insConfirmar.addEventListener("click", function () {
                const payload = {
                    codigo: insCodigo.value.trim(),
                    nombre: insNombre.value.trim(),
                    descripcion: insDescripcion.value.trim(),
                    unidad: insUnidad.value.trim(),
                    stock_inicial: insStock.value || "0"
                };

                if (!payload.codigo || !payload.nombre) {
                    alert("Código e Insumo son obligatorios.");
                    return;
                }

                fetch("/insumos/nuevo", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                })
                    .then(async r => {
                        if (r.ok) {
                            location.reload();
                        } else {
                            const errData = await r.json().catch(() => ({}));
                            alert("Error: " + (errData.error || "No se pudo agregar el insumo."));
                        }
                    })
                    .catch(err => alert("Error de conexión."));
            });
        }

        // ===== PAPEL BORRAR HISTORIAL =====
        document.addEventListener('click', function (e) {
            if (e.target.classList.contains('btn-borrar-papel')) {
                const btn = e.target;
                const id = btn.dataset.id;
                const tipo = btn.dataset.tipo;

                if (!confirm("¿Seguro que deseas borrar este registro del historial? Solo se borrará el registro, el inventario no se modificará.")) return;

                fetch('/papel/historial/eliminar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id, tipo: tipo })
                })
                    .then(r => r.json())
                    .then(data => {
                        if (data.ok) {
                            btn.closest('tr').remove();
                        } else {
                            alert("Error: " + data.error);
                        }
                    })
                    .catch(err => alert("Error de conexión"));
            }
        });

        // ===== PAPEL MODIFICAR =====
        const modalModPapel = document.getElementById('modal-papel-modificar-general');
        const btnGuardarModPapel = document.getElementById('btn-confirmar-mod-papel');
        const modPapelSelect = document.getElementById('mod-papel-select');

        document.addEventListener('click', function (e) {
            if (e.target.classList.contains('btn-modificar-papel-row')) {
                const btn = e.target;

                modPapelSelect.value = btn.dataset.id;
                document.getElementById('mod-papel-nombre').value = btn.dataset.nombre;
                document.getElementById('mod-papel-formato').value = btn.dataset.formato;
                document.getElementById('mod-papel-stock').value = btn.dataset.stock;
                document.getElementById('mod-papel-entradas').value = btn.dataset.entradas;
                document.getElementById('mod-papel-salidas').value = btn.dataset.salidas;

                if (modalModPapel) modalModPapel.style.display = 'flex';
            }
        });

        if (modPapelSelect) {
            modPapelSelect.addEventListener('change', function () {
                const selectedOption = modPapelSelect.options[modPapelSelect.selectedIndex];
                if (modPapelSelect.value) {
                    document.getElementById('mod-papel-nombre').value = selectedOption.dataset.nombre || '';
                    document.getElementById('mod-papel-formato').value = selectedOption.dataset.formato || '';
                    document.getElementById('mod-papel-stock').value = selectedOption.dataset.stock || '0';
                    document.getElementById('mod-papel-entradas').value = selectedOption.dataset.entradas || '0';
                    document.getElementById('mod-papel-salidas').value = selectedOption.dataset.salidas || '0';
                }
            });
        }

        if (btnGuardarModPapel) {
            btnGuardarModPapel.addEventListener('click', function () {
                const payload = {
                    id: modPapelSelect.value,
                    nombre: document.getElementById('mod-papel-nombre').value,
                    formato: document.getElementById('mod-papel-formato').value,
                    stock_inicial: document.getElementById('mod-papel-stock').value,
                    entradas: document.getElementById('mod-papel-entradas').value,
                    salidas: document.getElementById('mod-papel-salidas').value
                };

                fetch('/papel/modificar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                    .then(r => r.json())
                    .then(data => {
                        if (data.ok) location.reload();
                        else alert("Error: " + data.error);
                    });
            });
        }

        // ===== PAPEL AGREGAR Y ELIMINAR =====
        const btnAddPapel = document.getElementById('btn-confirmar-add-papel');

        if (btnAddPapel) {
            const newBtnAdd = btnAddPapel.cloneNode(true);
            btnAddPapel.parentNode.replaceChild(newBtnAdd, btnAddPapel);

            newBtnAdd.addEventListener('click', function () {
                const nombreInput = document.getElementById('add-papel-nombre');
                const formatoInput = document.getElementById('add-papel-formato');
                const stockInput = document.getElementById('add-papel-stock');

                const nombre = nombreInput ? nombreInput.value.trim() : "";
                const formato = formatoInput ? formatoInput.value : "";
                const stock = stockInput ? stockInput.value : "0";

                if (!nombre || !formato) {
                    alert("Por favor, completá nombre y formato.");
                    return;
                }

                fetch('/papel/agregar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre: nombre, formato: formato, stock: stock })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.ok) {
                            location.reload();
                        } else {
                            alert("Error: " + (data.error || "No se pudo agregar"));
                        }
                    })
                    .catch(err => alert("Error de conexión al agregar."));
            });
        }

        const btnDelPapel = document.getElementById('btn-confirmar-del-papel');

        if (btnDelPapel) {
            const newBtnDel = btnDelPapel.cloneNode(true);
            btnDelPapel.parentNode.replaceChild(newBtnDel, btnDelPapel);

            newBtnDel.addEventListener('click', function () {
                const selectDel = document.getElementById('del-papel-select');
                const idPapel = selectDel ? selectDel.value : "";

                if (!idPapel) {
                    alert("Tenés que seleccionar un papel de la lista.");
                    return;
                }

                if (!confirm("¿ESTÁS SEGURO? Se eliminará el papel y todo su historial de entradas y salidas.")) {
                    return;
                }

                fetch('/papel/eliminar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: idPapel })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.ok) {
                            location.reload();
                        } else {
                            alert("Error al eliminar: " + (data.error || "Desconocido"));
                        }
                    })
                    .catch(err => alert("Error de conexión al eliminar."));
            });
        }

        // ===== PAPEL FILTROS - ENFOQUE SIMPLE (SOLO TEXTO) =====

        // ADMIN
        const papelInput = document.getElementById("filtro-papel");
        const papelTable = document.getElementById("tabla-papel");

        if (papelInput && papelTable) {
            const filtrarPapelAdmin = function () {
                const busqueda = papelInput.value.toLowerCase().trim();
                const filas = papelTable.querySelectorAll("tbody tr");

                const checkStock = document.getElementById("check-stock-papel");
                const soloConStock = checkStock ? checkStock.checked : false;

                filas.forEach(function (fila) {
                    let mostrar = true;

                    // Filtro de texto
                    if (busqueda) {
                        const textoFila = fila.textContent.toLowerCase();
                        if (!textoFila.includes(busqueda)) {
                            mostrar = false;
                        }
                    }

                    // Filtro de stock: Columna índice 6 (0:ID, 1:Nombre, 2:Formato, 3:StockIni, 4:Ent, 5:Sal, 6:Total)
                    if (soloConStock && mostrar) {
                        const celdaTotal = fila.cells[6];
                        if (celdaTotal) {
                            const totalVal = parseInt(celdaTotal.textContent.trim()) || 0;
                            if (totalVal <= 0) {
                                mostrar = false;
                            }
                        }
                    }

                    fila.style.display = mostrar ? "" : "none";
                });
            };

            papelInput.addEventListener("input", filtrarPapelAdmin);
            papelInput.addEventListener("keyup", filtrarPapelAdmin);

            const checkStock = document.getElementById("check-stock-papel");
            if (checkStock) {
                checkStock.addEventListener("change", filtrarPapelAdmin);
            }
        }

        // SIMPLE
        const papelSimpleInput = document.getElementById("filtro-papel-simple");
        const papelSimpleTable = document.getElementById("tabla-papel-simple");

        if (papelSimpleInput && papelSimpleTable) {
            const filtrarPapelSimple = function () {
                const busqueda = papelSimpleInput.value.toLowerCase().trim();
                const filas = papelSimpleTable.querySelectorAll("tbody tr");

                filas.forEach(function (fila) {
                    let mostrar = true;

                    // Filtro de texto
                    if (busqueda) {
                        const textoFila = fila.textContent.toLowerCase();
                        if (!textoFila.includes(busqueda)) {
                            mostrar = false;
                        }
                    }

                    fila.style.display = mostrar ? "" : "none";
                });
            };

            papelSimpleInput.addEventListener("input", filtrarPapelSimple);
            papelSimpleInput.addEventListener("keyup", filtrarPapelSimple);
        }

    });

    // ===== FUNCIONES GLOBALES =====
    function openModal(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = "flex";
    }
    function closeModal(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = "none";
    }
    function abrirModalEliminarInsumo() {
        const m = document.getElementById("modal-insumo-eliminar");
        if (m) m.style.display = "flex";
    }
    function cerrarModalEliminarInsumo() {
        const m = document.getElementById("modal-insumo-eliminar");
        if (m) m.style.display = "none";
    }
    const tablaInventario = document.getElementById("tabla-inventario");
    const filtroInv = document.getElementById("filtro-inventario");
    if (tablaInventario && filtroInv) {
        filtroInv.addEventListener("input", function () {
            const filtro = filtroInv.value.trim().toLowerCase();
            const filas = tablaInventario.querySelectorAll("tbody tr");
            filas.forEach((tr) => {
                const texto = tr.textContent.toLowerCase();
                tr.style.display = (!filtro || texto.includes(filtro)) ? "" : "none";
            });
        });
    }

    const tablaInventarioSimple = document.getElementById("tabla-inventario-simple");
    const filtroInvSimple = document.getElementById("filtro-inventario-simple");
    if (tablaInventarioSimple && filtroInvSimple) {
        filtroInvSimple.addEventListener("input", function () {
            const filtro = filtroInvSimple.value.trim().toLowerCase();
            const filas = tablaInventarioSimple.querySelectorAll("tbody tr");
            filas.forEach((tr) => {
                const texto = tr.textContent.toLowerCase();
                tr.style.display = (!filtro || texto.includes(filtro)) ? "" : "none";
            });
        });
    }

    // -------------------
    // INVENTARIO: MODIFICAR CANTIDADES
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
        });

        invConfirmar.addEventListener("click", function () {
            if (!inventarioIdActual) return;
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
                .then(r => r.json())
                .then(data => {
                    if (!data.ok) throw new Error("Error");
                    const celdas = inventarioFilaActual.querySelectorAll("td");
                    celdas[3].textContent = data.stock_inicial;
                    celdas[4].textContent = data.entradas;
                    celdas[5].textContent = data.salidas;
                    celdas[6].textContent = data.total;
                    const btn = inventarioFilaActual.querySelector(".btn-modificar");
                    btn.dataset.stock = data.stock_inicial;
                    btn.dataset.entradas = data.entradas;
                    btn.dataset.salidas = data.salidas;
                    btn.dataset.total = data.total;
                    modalInv.style.display = "none";
                })
                .catch(e => alert("No se pudo actualizar."));
        });
    }

    // -------------------
    // INVENTARIO: ELIMINAR INSUMO (Lógica Interna)
    // -------------------
    const delSelect = document.getElementById("del-insumo-select");
    const delEliminar = document.getElementById("del-insumo-eliminar");
    const modalDelConfirm = document.getElementById("modal-insumo-confirm");
    const delConfSi = document.getElementById("insumo-conf-si");
    const delConfNo = document.getElementById("insumo-conf-no");
    let codigoAEliminar = null;

    if (delEliminar && modalDelConfirm) {
        delEliminar.addEventListener("click", function () {
            const codigo = delSelect.value;
            if (!codigo) {
                alert("Seleccione un insumo.");
                return;
            }
            codigoAEliminar = codigo;
            modalDelConfirm.style.display = "flex";
        });

        delConfNo.addEventListener("click", function () {
            modalDelConfirm.style.display = "none";
            codigoAEliminar = null;
        });

        delConfSi.addEventListener("click", function () {
            if (!codigoAEliminar) return;
            fetch(`/insumos/${codigoAEliminar}/eliminar`, { method: "POST" })
                .then(r => r.json())
                .then(data => {
                    if (!data.ok) throw new Error("Error");
                    location.reload(); // Recargar para ver cambios
                })
                .catch(() => alert("Error al eliminar."));
        });
    }

    // -------------------
    // INVENTARIO: MODIFICAR DATOS INSUMO
    // -------------------
    const modalEditInsumo = document.getElementById("modal-insumo-editar");
    const editCerrar = document.getElementById("edit-insumo-cerrar");
    const editConfirmar = document.getElementById("edit-insumo-confirmar");
    const editSelectInsumo = document.getElementById("edit-insumo-select");

    if (modalEditInsumo && editSelectInsumo) {
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

        editSelectInsumo.addEventListener("change", cargarDatosEdicion);
        // Cargar datos iniciales al abrir se maneja via onclick en HTML, 
        // pero necesitamos el listener aqui si se cambia el select.

        if (editCerrar) {
            editCerrar.addEventListener("click", () => modalEditInsumo.style.display = "none");
        }

        if (editConfirmar) {
            editConfirmar.addEventListener("click", function () {
                const payload = {
                    codigo_original: editSelectInsumo.value,
                    codigo_nuevo: editCodigo.value.trim(),
                    nombre: editNombre.value.trim(),
                    descripcion: editDescripcion.value.trim(),
                    unidad: editUnidad.value.trim(),
                };
                if (!payload.codigo_nuevo || !payload.nombre) return alert("Faltan datos");

                fetch("/insumos/modificar", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                })
                    .then(r => r.json())
                    .then(data => {
                        if (!data.ok) throw new Error(data.error);
                        location.reload();
                    })
                    .catch(e => alert(e.message));
            });
        }
    }

    // -------------------
    // INVENTARIO: AGREGAR INSUMO (Corregido Definitivo)
    // -------------------
    const modalInsumo = document.getElementById("modal-insumo");
    const insCerrar = document.getElementById("insumo-modal-cerrar");
    const insConfirmar = document.getElementById("insumo-modal-confirmar");

    // Inputs del modal
    const insCodigo = document.getElementById("ins-codigo");
    const insNombre = document.getElementById("ins-nombre");
    const insDescripcion = document.getElementById("ins-descripcion");
    const insUnidad = document.getElementById("ins-unidad");
    const insStock = document.getElementById("ins-stock");

    if (modalInsumo && insConfirmar) {
        // Cerrar modal
        if (insCerrar) {
            insCerrar.addEventListener("click", () => modalInsumo.style.display = "none");
        }

        // Confirmar guardado
        insConfirmar.addEventListener("click", function () {
            const payload = {
                codigo: insCodigo.value.trim(),
                nombre: insNombre.value.trim(),
                descripcion: insDescripcion.value.trim(),
                unidad: insUnidad.value.trim(),
                stock_inicial: insStock.value || "0" // CAMBIO: Debe llamarse stock_inicial
            };

            if (!payload.codigo || !payload.nombre) {
                alert("Código e Insumo son obligatorios.");
                return;
            }

            // CAMBIO: La ruta correcta en tu Python es /insumos/nuevo
            fetch("/insumos/nuevo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then(async r => {
                    if (r.ok) {
                        location.reload();
                    } else {
                        // Intentamos leer el error real del servidor
                        const errData = await r.json().catch(() => ({}));
                        alert("Error: " + (errData.error || "No se pudo agregar el insumo."));
                    }
                })
                .catch(err => alert("Error de conexión."));
        });
    }

    // --------------------------------
    // PEDIDOS: REGISTRAR NUEVO (Lógica JS)
    // --------------------------------
    const insumoPedidoInput = document.getElementById("insumo_pedido");
    const insumoCodigoHidden = document.getElementById("insumo_codigo");
    const btnPedidoConfirmar = document.getElementById("btn-pedido-confirmar");
    const modalPedidoPrevia = document.getElementById("modal-pedido-previa");
    const pedidoPreviaCancelar = document.getElementById("pedido-previa-cancelar");

    if (insumoPedidoInput && insumoCodigoHidden) {
        insumoPedidoInput.addEventListener("input", function () {
            const val = this.value;
            const lista = document.getElementById("lista-insumos-pedido");
            let codigo = "";
            if (lista) {
                for (const opt of lista.options) {
                    if (opt.value === val) {
                        codigo = opt.dataset.codigo || "";
                        break;
                    }
                }
            }
            insumoCodigoHidden.value = codigo;
        });
    }

    if (btnPedidoConfirmar && modalPedidoPrevia) {
        btnPedidoConfirmar.addEventListener("click", function () {
            // Validacion simple visual
            const ids = ["pedido_por", "proveedor", "insumo_pedido", "presentacion", "descripcion_pedido", "cantidad_pedido"];
            let error = false;
            ids.forEach(id => {
                const el = document.getElementById(id);
                const err = document.getElementById("err-" + id);
                if (el && !el.value.trim()) {
                    if (err) err.textContent = "Campo requerido";
                    error = true;
                } else if (err) {
                    err.textContent = "";
                }
            });
            if (error) return;

            // Rellenar previa
            document.getElementById("prev-pedido-por").textContent = document.getElementById("pedido_por").value;
            document.getElementById("prev-pedido-proveedor").textContent = document.getElementById("proveedor").value;
            document.getElementById("prev-pedido-insumo").textContent = document.getElementById("insumo_pedido").value;
            document.getElementById("prev-pedido-presentacion").textContent = document.getElementById("presentacion").value;
            document.getElementById("prev-pedido-descripcion").textContent = document.getElementById("descripcion_pedido").value;
            document.getElementById("prev-pedido-cantidad").textContent = document.getElementById("cantidad_pedido").value;
            document.getElementById("prev-pedido-fecha").textContent = new Date().toLocaleDateString("es-AR");

            modalPedidoPrevia.style.display = "flex";
        });

        if (pedidoPreviaCancelar) {
            pedidoPreviaCancelar.addEventListener("click", () => modalPedidoPrevia.style.display = "none");
        }
    }

    // Filtros Pedidos
    const filtroPedidos = document.getElementById("filtro-pedidos");
    const tablaPedidos = document.getElementById("tabla-pedidos");
    if (filtroPedidos && tablaPedidos) {
        filtroPedidos.addEventListener("input", function () {
            const q = this.value.toLowerCase();
            tablaPedidos.querySelectorAll("tbody tr").forEach(tr => {
                tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
            });
        });
    }

    // Boton Entregado Papel
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('btn-entregado-papel')) {
            const btn = e.target;
            const id = btn.dataset.id;
            if (!id || btn.disabled) return;

            fetch(`/papel/pedidos/${id}/entregado`, { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.ok) {
                        const fila = btn.closest('tr');
                        if (fila) {
                            fila.classList.add('pedido-entregado');
                            fila.querySelector('.estado-pedido').textContent = 'Entregado';
                        }
                        btn.disabled = true;
                        btn.textContent = "✔";
                    }
                });
        }
    });

    // Filtros Papel
    const filtroPapel = document.getElementById("filtro-papel");
    const tablaPapel = document.getElementById("tabla-papel");
    if (filtroPapel && tablaPapel) {
        filtroPapel.addEventListener("input", function () {
            const q = this.value.toLowerCase();
            tablaPapel.querySelectorAll("tbody tr").forEach(tr => {
                tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
            });
        });
    }
});

// FUNCIONES GLOBALES (Fuera del DOMContentLoaded para que funcionen con onclick="")
function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = "flex";
}
function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
}
function abrirModalEliminarInsumo() {
    const m = document.getElementById("modal-insumo-eliminar");
    if (m) m.style.display = "flex";
}
function cerrarModalEliminarInsumo() {
    const m = document.getElementById("modal-insumo-eliminar");
    if (m) m.style.display = "none";
}

// ============================================
// GESTIÓN PAPEL: BORRAR HISTORIAL Y MODIFICAR
// ============================================

// 1. BORRAR HISTORIAL PAPEL (Entradas/Salidas)
// Delegación de eventos para los botones de la tabla
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('btn-borrar-papel')) {
        const btn = e.target;
        const id = btn.dataset.id;
        const tipo = btn.dataset.tipo; // "entrada" o "salida"

        if (!confirm("¿Seguro que deseas borrar este registro del historial? Solo se borrará el registro, el inventario no se modificará.")) return;

        fetch('/papel/historial/eliminar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, tipo: tipo })
        })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    // Borrar fila visualmente o recargar
                    btn.closest('tr').remove();
                } else {
                    alert("Error: " + data.error);
                }
            })
            .catch(err => alert("Error de conexión"));
    }
});

// 2. MODIFICAR PAPEL (Botón en la fila)
const modalModPapel = document.getElementById('modal-papel-modificar-general');
const btnGuardarModPapel = document.getElementById('btn-confirmar-mod-papel');
const modPapelSelect = document.getElementById('mod-papel-select');

// Al hacer clic en "MODIFICAR" en la tabla
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('btn-modificar-papel-row')) {
        const btn = e.target;

        // Llenar el modal con los datos del botón
        modPapelSelect.value = btn.dataset.id;
        document.getElementById('mod-papel-nombre').value = btn.dataset.nombre;
        document.getElementById('mod-papel-stock').value = btn.dataset.stock;
        document.getElementById('mod-papel-entradas').value = btn.dataset.entradas;
        document.getElementById('mod-papel-salidas').value = btn.dataset.salidas;

        // Abrir modal
        if (modalModPapel) modalModPapel.style.display = 'flex';
    }
});

// Cargar datos cuando se cambia el select
if (modPapelSelect) {
    modPapelSelect.addEventListener('change', function () {
        const selectedOption = modPapelSelect.options[modPapelSelect.selectedIndex];
        if (modPapelSelect.value) {
            document.getElementById('mod-papel-nombre').value = selectedOption.dataset.nombre || '';
            document.getElementById('mod-papel-stock').value = selectedOption.dataset.stock || '0';
            document.getElementById('mod-papel-entradas').value = selectedOption.dataset.entradas || '0';
            document.getElementById('mod-papel-salidas').value = selectedOption.dataset.salidas || '0';
        }
    });
}

// Al hacer clic en "Guardar Cambios" dentro del modal
if (btnGuardarModPapel) {
    btnGuardarModPapel.addEventListener('click', function () {
        const payload = {
            id: modPapelSelect.value,
            nombre: document.getElementById('mod-papel-nombre').value,
            stock_inicial: document.getElementById('mod-papel-stock').value,
            entradas: document.getElementById('mod-papel-entradas').value,
            salidas: document.getElementById('mod-papel-salidas').value
        };

        fetch('/papel/modificar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.ok) location.reload();
                else alert("Error: " + data.error);
            });
    });
}

// =========================================================
// CORRECCIÓN: FUNCIONES ADMIN PAPEL (Agregar y Eliminar)
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    // --- 1. LÓGICA PARA AGREGAR PAPEL ---
    const btnAddPapel = document.getElementById('btn-confirmar-add-papel');

    if (btnAddPapel) {
        // Clonamos el botón para eliminar eventos viejos que no funcionen
        const newBtnAdd = btnAddPapel.cloneNode(true);
        btnAddPapel.parentNode.replaceChild(newBtnAdd, btnAddPapel);

        newBtnAdd.addEventListener('click', function () {
            const nombreInput = document.getElementById('add-papel-nombre');
            const stockInput = document.getElementById('add-papel-stock');

            const nombre = nombreInput ? nombreInput.value.trim() : "";
            const stock = stockInput ? stockInput.value : "0";

            if (!nombre) {
                alert("Por favor, escribí un nombre para el papel.");
                return;
            }

            // Enviar al servidor
            fetch('/papel/agregar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre: nombre, stock: stock })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.ok) {
                        location.reload(); // Recargar para ver el nuevo papel
                    } else {
                        alert("Error: " + (data.error || "No se pudo agregar"));
                    }
                })
                .catch(err => alert("Error de conexión al agregar."));
        });
    }

    // --- 2. LÓGICA PARA ELIMINAR PAPEL ---
    const btnDelPapel = document.getElementById('btn-confirmar-del-papel');

    if (btnDelPapel) {
        // Clonamos para limpiar eventos anteriores
        const newBtnDel = btnDelPapel.cloneNode(true);
        btnDelPapel.parentNode.replaceChild(newBtnDel, btnDelPapel);

        newBtnDel.addEventListener('click', function () {
            const selectDel = document.getElementById('del-papel-select');
            const idPapel = selectDel ? selectDel.value : "";

            if (!idPapel) {
                alert("Tenés que seleccionar un papel de la lista.");
                return;
            }

            // AQUI ESTA EL POPUP QUE PEDISTE
            if (!confirm("¿ESTÁS SEGURO? Se eliminará el papel y todo su historial de entradas y salidas.")) {
                return; // Si dice que no, cancelamos todo
            }

            // Enviar al servidor
            fetch('/papel/eliminar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: idPapel })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.ok) {
                        location.reload(); // Recargar para ver que desapareció
                    } else {
                        alert("Error al eliminar: " + (data.error || "Desconocido"));
                    }
                })
                .catch(err => alert("Error de conexión al eliminar."));
        });
    }
});

// ===== BORRAR HISTORIAL (ENTRADAS / SALIDAS GENERALES) =====
// Se usa delegación al document, fuera del DOMContentLoaded, para asegurar que capte todo.
document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-borrar");

    // Si no es botón borrar, o es el de papel (que ya tiene su lógica), no hacemos nada.
    if (!btn || btn.classList.contains("btn-borrar-papel")) return;

    const id = btn.dataset.id;
    const tipo = btn.dataset.tipo; // "entrada" o "salida"

    if (!id || !tipo) return;

    if (!confirm("¿Seguro que deseas borrar este registro de historial?")) return;

    const url = (tipo === "entrada")
        ? `/entradas/${id}/borrar`
        : `/salidas/${id}/borrar`;

    fetch(url, {
        method: "POST"
    })
        .then(function (response) {
            if (response.ok) {
                // Eliminar la fila visualmente o recargar
                location.reload();
            } else {
                alert("Error al borrar el registro (status " + response.status + ")");
            }
        })
        .catch(function (err) {
            console.error(err);
            alert("Error de conexión al intentar borrar.");
        });
});

// ==========================================
// PEGAR AL FINAL DE main.js
// LOGICA FILTRO "CON STOCK" (PAPEL)
// ==========================================

function initFiltroPapel(checkId, inputId, tableId, colIndexTotal) {
    const chk = document.getElementById(checkId);
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);

    if (!chk || !table) return;

    function filtrar() {
        const soloStock = chk.checked;
        const termino = input ? input.value.toLowerCase() : "";
        const filas = table.querySelectorAll("tbody tr");

        filas.forEach(tr => {
            let mostrar = true;

            // 1. Respetar el Filtro de Texto (si el usuario escribió algo)
            if (termino) {
                const textoFila = tr.textContent.toLowerCase();
                if (!textoFila.includes(termino)) {
                    mostrar = false;
                }
            }

            // 2. Aplicar Filtro de Stock (si el checkbox está marcado)
            if (mostrar && soloStock) {
                const celdas = tr.querySelectorAll("td");
                // Buscamos la columna TOTAL usando el índice
                if (celdas[colIndexTotal]) {
                    const valor = parseInt(celdas[colIndexTotal].textContent.trim()) || 0;
                    // Si es menor a 1 (o sea 0 o negativo), lo ocultamos
                    if (valor < 1) {
                        mostrar = false;
                    }
                }
            }

            tr.style.display = mostrar ? "" : "none";
        });
    }

    // Escuchar cambios en el checkbox
    chk.addEventListener("change", filtrar);

    // Escuchar cambios en el input de texto para que trabajen juntos
    if (input) {
        input.addEventListener("input", filtrar);
    }
}

// Inicializar Papel Simple (La columna TOTAL es la 5ta -> índice 4)
document.addEventListener("DOMContentLoaded", function () {
    initFiltroPapel("check-stock-papel-simple", "filtro-papel-simple", "tabla-papel-simple", 5);

    // Inicializar Papel Admin (La columna TOTAL es la 8va -> índice 7)
    initFiltroPapel("check-stock-papel", "filtro-papel", "tabla-papel", 6);
});