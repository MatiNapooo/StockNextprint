document.addEventListener("DOMContentLoaded", function () {

  /* ============================================================
     1) BORRAR EN HISTORIALES (ENTRADAS / SALIDAS)
     - HTML usa: #modal-borrar + botones .modal-btn-si / .modal-btn-no
     - Botones por fila: .btn-borrar con data-id y data-tipo
  ============================================================ */

  const modalBorrar = document.getElementById("modal-borrar");
  const btnSi = modalBorrar ? modalBorrar.querySelector(".modal-btn-si") : null;
  const btnNo = modalBorrar ? modalBorrar.querySelector(".modal-btn-no") : null;

  let borrarPendiente = { id: null, tipo: null, row: null };

  document.querySelectorAll(".btn-borrar").forEach(btn => {
    btn.addEventListener("click", function () {
      borrarPendiente.id = this.dataset.id;
      borrarPendiente.tipo = this.dataset.tipo; // "entrada" o "salida"
      borrarPendiente.row = this.closest("tr");

      if (modalBorrar) modalBorrar.style.display = "flex";
    });
  });

  if (btnNo) {
    btnNo.addEventListener("click", function () {
      if (modalBorrar) modalBorrar.style.display = "none";
      borrarPendiente = { id: null, tipo: null, row: null };
    });
  }

  if (btnSi) {
    btnSi.addEventListener("click", async function () {
      if (!borrarPendiente.id || !borrarPendiente.tipo) return;

      let url = "";
      if (borrarPendiente.tipo === "entrada") {
        url = `/entradas/${borrarPendiente.id}/borrar`;
      } else if (borrarPendiente.tipo === "salida") {
        url = `/salidas/${borrarPendiente.id}/borrar`;
      } else {
        return;
      }

      try {
        const resp = await fetch(url, { method: "POST" });
        if (resp.ok) {
          if (borrarPendiente.row) borrarPendiente.row.remove();
        }
      } catch (e) {
        console.error("Error borrando registro:", e);
      }

      if (modalBorrar) modalBorrar.style.display = "none";
      borrarPendiente = { id: null, tipo: null, row: null };
    });
  }


  /* ============================================================
     2) MODALES DE VISTA PREVIA (ENTRADAS / SALIDAS / PEDIDOS)
     - Alineado a los IDs reales:
       Entradas: #entrada-vista-previa, cancel: #entrada-previa-cancelar
       Salidas : #salida-vista-previa,  cancel: #salida-previa-cancelar
       Pedidos : #pedido-vista-previa,  cancel: #pedido-previa-cancelar
  ============================================================ */

  function cerrarModal(idModal) {
    const m = document.getElementById(idModal);
    if (m) m.style.display = "none";
  }

  const entradaCancelar = document.getElementById("entrada-previa-cancelar");
  if (entradaCancelar) entradaCancelar.addEventListener("click", () => cerrarModal("entrada-vista-previa"));

  const salidaCancelar = document.getElementById("salida-previa-cancelar");
  if (salidaCancelar) salidaCancelar.addEventListener("click", () => cerrarModal("salida-vista-previa"));

  const pedidoCancelar = document.getElementById("pedido-previa-cancelar");
  if (pedidoCancelar) pedidoCancelar.addEventListener("click", () => cerrarModal("pedido-vista-previa"));


  /* ============================================================
     3) INSUMOS (ADMIN): Agregar / Modificar / Eliminar
     - IDs reales en tu HTML:
       Agregar: #insumo-modal-confirmar (abre confirmación) 
               y se confirma con #insumo-conf-si
       Eliminar: select #del-insumo-select + btn #del-insumo-eliminar
       Modificar: select #edit-insumo-select + btn #edit-insumo-guardar
  ============================================================ */

  // --------- AGREGAR INSUMO ----------
  const btnAgregarConfirmar = document.getElementById("insumo-modal-confirmar");
  const modalConfirmAgregar = document.getElementById("modal-insumo-confirm");
  const btnAgregarSi = document.getElementById("insumo-conf-si");
  const btnAgregarNo = document.getElementById("insumo-conf-no");

  if (btnAgregarConfirmar && modalConfirmAgregar) {
    btnAgregarConfirmar.addEventListener("click", function () {
      // abre confirmación
      modalConfirmAgregar.style.display = "flex";
    });
  }

  if (btnAgregarNo && modalConfirmAgregar) {
    btnAgregarNo.addEventListener("click", function () {
      modalConfirmAgregar.style.display = "none";
    });
  }

  if (btnAgregarSi) {
    btnAgregarSi.addEventListener("click", async function () {
      const codigo = (document.getElementById("ins-codigo") || {}).value || "";
      const nombre = (document.getElementById("ins-nombre") || {}).value || "";
      const descripcion = (document.getElementById("ins-descripcion") || {}).value || "";
      const stock = parseInt(((document.getElementById("ins-stock") || {}).value || "0"), 10);
      const unidad = (document.getElementById("ins-unidad") || {}).value || "";

      if (!codigo.trim() || !nombre.trim() || !descripcion.trim()) return;

      try {
        const resp = await fetch("/insumo/agregar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ codigo, nombre, descripcion, stock, unidad })
        });

        if (resp.ok) {
          window.location.reload();
        }
      } catch (e) {
        console.error("Error agregando insumo:", e);
      }
    });
  }


  // --------- ELIMINAR INSUMO ----------
  const btnEliminar = document.getElementById("del-insumo-eliminar");
  if (btnEliminar) {
    btnEliminar.addEventListener("click", async function () {
      const sel = document.getElementById("del-insumo-select");
      const codigo = sel ? sel.value : "";
      if (!codigo) return;

      try {
        const resp = await fetch(`/insumos/${codigo}/eliminar`, { method: "POST" });
        if (resp.ok) window.location.reload();
      } catch (e) {
        console.error("Error eliminando insumo:", e);
      }
    });
  }


  // --------- MODIFICAR INSUMO ----------
  const btnGuardarEdit = document.getElementById("edit-insumo-guardar");
  if (btnGuardarEdit) {
    btnGuardarEdit.addEventListener("click", async function () {
      const sel = document.getElementById("edit-insumo-select");
      const codigo = sel ? sel.value : "";
      if (!codigo) return;

      const nombre = (document.getElementById("edit-nombre") || {}).value || "";
      const descripcion = (document.getElementById("edit-desc") || {}).value || "";
      const unidad = (document.getElementById("edit-unidad") || {}).value || "";

      try {
        const resp = await fetch(`/insumos/${codigo}/modificar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nombre, descripcion, unidad })
        });

        if (resp.ok) window.location.reload();
      } catch (e) {
        console.error("Error modificando insumo:", e);
      }
    });
  }


  /* ============================================================
     4) PEDIDOS: completar insumo_codigo con datalist
     - IDs reales:
       input #pedido-insumo
       datalist #insumos-list
       hidden #pedido-insumo-codigo
  ============================================================ */

  const pedidoInsumo = document.getElementById("pedido-insumo");
  const pedidoCodigo = document.getElementById("pedido-insumo-codigo");
  const lista = document.getElementById("insumos-list");

  if (pedidoInsumo && pedidoCodigo && lista) {
    pedidoInsumo.addEventListener("input", function () {
      const val = this.value.trim();
      const opt = Array.from(lista.options).find(o => o.value === val);
      pedidoCodigo.value = opt ? (opt.dataset.codigo || "") : "";
    });
  }

});
