document.addEventListener("DOMContentLoaded", function () {
    const confirmButton = document.querySelector(".confirm-button");
    const previewSection = document.getElementById("preview-section");
    const previewWrapper = document.getElementById("preview-table-wrapper");
    const insumoSelect = document.getElementById("insumo_seleccionado");
    const unidadSelect = document.getElementById("unidad_seleccionada");

    const errorInsumo = document.getElementById("error-insumo");
    const errorUnidad = document.getElementById("error-unidad");

    if (
        !confirmButton ||
        !previewSection ||
        !previewWrapper ||
        !insumoSelect ||
        !unidadSelect ||
        !errorInsumo ||
        !errorUnidad
    ) {
        return;
    }

    confirmButton.addEventListener("click", function () {
        // Limpiar errores anteriores
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

        // Si falta algo, no generamos vista previa
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
            month: "short"
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

    const finishButton = document.querySelector(".finish-button");
    if (finishButton) {
        finishButton.addEventListener("click", function () {
            alert("Más adelante este botón va a guardar el registro en la base de datos.");
        });
    }
});
