const saleForm = document.querySelector("[data-sale-form]");

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js");
  });
}

document.querySelectorAll("[data-photo-capture]").forEach((widget) => {
  const video = widget.querySelector("video");
  const canvas = widget.querySelector("canvas");
  const input = widget.querySelector('input[name="foto_base64"]');
  const startButton = widget.querySelector("[data-photo-start]");
  const takeButton = widget.querySelector("[data-photo-take]");

  startButton.addEventListener("click", async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    video.srcObject = stream;
  });

  takeButton.addEventListener("click", () => {
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    input.value = canvas.toDataURL("image/png");
    canvas.style.display = "block";
  });
});

if (saleForm) {
  const totalEl = document.querySelector("[data-sale-total]");
  const clientSelect = document.querySelector("[data-client-select]");
  const clientPhoto = document.querySelector("[data-client-photo]");
  const clientDocument = document.querySelector("[data-client-document]");
  const formatter = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

  function updateTotal() {
    let total = 0;
    document.querySelectorAll(".sale-item").forEach((row) => {
      const checkbox = row.querySelector('input[type="checkbox"]');
      const quantity = row.querySelector('input[type="number"]');
      if (checkbox.checked) {
        total += Number(checkbox.dataset.price.replace(",", ".")) * Number(quantity.value || 1);
      }
    });
    totalEl.textContent = formatter.format(total);
  }

  document.querySelectorAll(".sale-item input").forEach((input) => {
    input.addEventListener("input", updateTotal);
    input.addEventListener("change", updateTotal);
  });

  function updateClientPreview() {
    const selected = clientSelect.options[clientSelect.selectedIndex];
    const photo = selected.dataset.photo;
    const documentNumber = selected.dataset.document;
    clientPhoto.innerHTML = photo ? `<img src="${photo}" alt="Foto cadastrada do cliente">` : "Sem foto";
    clientDocument.textContent = documentNumber
      ? `Documento/prontuário: ${documentNumber}`
      : "Documento opcional não informado.";
  }

  clientSelect.addEventListener("change", updateClientPreview);

  const video = document.getElementById("camera");
  const canvas = document.getElementById("snapshot");
  const photoInput = document.getElementById("foto_base64");
  const startButton = document.querySelector("[data-start-camera]");
  const takeButton = document.querySelector("[data-take-photo]");

  startButton.addEventListener("click", async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
      audio: false,
    });
    video.srcObject = stream;
  });

  takeButton.addEventListener("click", () => {
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    photoInput.value = canvas.toDataURL("image/png");
    canvas.style.display = "block";
  });

  updateTotal();
  updateClientPreview();
}
