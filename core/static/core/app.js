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
  const balanceAfterEl = document.querySelector("[data-sale-balance-after]");
  const clientSelect = document.querySelector("[data-client-select]");
  const clientPhoto = document.querySelector("[data-client-photo]");
  const clientDocument = document.querySelector("[data-client-document]");
  const itemSelect = document.querySelector("[data-sale-item-select]");
  const itemQuantity = document.querySelector("[data-sale-item-quantity]");
  const addItemButton = document.querySelector("[data-sale-add-item]");
  const saleLines = document.querySelector("[data-sale-lines]");
  const saleHidden = document.querySelector("[data-sale-hidden]");
  const saleEmpty = document.querySelector("[data-sale-empty]");
  const formatter = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const selectedItems = new Map();

  function parseNumber(value) {
    return Number(String(value || "0").replace(",", "."));
  }

  function updateTotal() {
    let total = 0;
    selectedItems.forEach((item) => {
      total += item.price * item.quantity;
    });
    totalEl.textContent = formatter.format(total);
    const selectedClient = clientSelect.options[clientSelect.selectedIndex];
    const balance = parseNumber(selectedClient?.dataset.balance);
    balanceAfterEl.textContent = formatter.format(balance - total);
    balanceAfterEl.classList.toggle("negative", balance - total < 0);
  }

  function renderSelectedItems() {
    saleLines.innerHTML = "";
    saleHidden.innerHTML = "";
    saleEmpty.style.display = selectedItems.size ? "none" : "block";

    selectedItems.forEach((item) => {
      const line = document.createElement("div");
      line.className = "sale-line";
      line.innerHTML = `
        <span><strong>${item.name}</strong><small>${formatter.format(item.price)} x ${item.quantity}</small></span>
        <strong>${formatter.format(item.price * item.quantity)}</strong>
        <button type="button" class="ghost-button" data-remove-item="${item.id}">Remover</button>
      `;
      saleLines.appendChild(line);

      const itemInput = document.createElement("input");
      itemInput.type = "hidden";
      itemInput.name = "itens";
      itemInput.value = item.id;
      saleHidden.appendChild(itemInput);

      const quantityInput = document.createElement("input");
      quantityInput.type = "hidden";
      quantityInput.name = `quantidade_${item.id}`;
      quantityInput.value = item.quantity;
      saleHidden.appendChild(quantityInput);
    });

    saleLines.querySelectorAll("[data-remove-item]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedItems.delete(button.dataset.removeItem);
        renderSelectedItems();
      });
    });

    updateTotal();
  }

  addItemButton?.addEventListener("click", () => {
    const selected = itemSelect.options[itemSelect.selectedIndex];
    if (!selected) return;

    const id = selected.value;
    const current = selectedItems.get(id);
    const stock = Number(selected.dataset.stock || 0);
    const requestedQuantity = Math.max(1, Number(itemQuantity.value || 1));
    const nextQuantity = Math.min(stock, (current?.quantity || 0) + requestedQuantity);

    selectedItems.set(id, {
      id,
      name: selected.dataset.name,
      price: parseNumber(selected.dataset.price),
      quantity: nextQuantity,
      stock,
    });
    itemQuantity.value = 1;
    renderSelectedItems();
  });

  saleForm.addEventListener("submit", (event) => {
    if (selectedItems.size === 0) {
      event.preventDefault();
      alert("Selecione pelo menos um item antes de finalizar a venda.");
    }
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
  clientSelect.addEventListener("change", updateTotal);

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
  renderSelectedItems();
  updateClientPreview();
}
