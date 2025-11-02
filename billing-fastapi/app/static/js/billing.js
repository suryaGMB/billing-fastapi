document.addEventListener("DOMContentLoaded", () => {
  const itemsContainer = document.getElementById("items-container");
  const addItemBtn = document.getElementById("add-item");
  const generateBtn = document.getElementById("generate-bill");
  const viewPurchases = document.getElementById("view-purchases");
  const resultEl = document.getElementById("result");
  const denomContainer = document.getElementById("denominations");

  const denomValues = [2000,500,200,100,50,20,10,5,2,1];

  function addProductRow(code = "", qty = 1) {
    const div = document.createElement("div");
    div.className = "items-row";
    div.innerHTML = `
      <input type="text" class="product-code" placeholder="Product ID (e.g. P001)" value="${code}" required />
      <input type="number" class="product-qty" min="1" value="${qty}" required />
      <button class="remove-row">Remove</button>
    `;
    div.querySelector(".remove-row").addEventListener("click", (e) => {
      e.preventDefault();
      div.remove();
    });
    itemsContainer.appendChild(div);
  }

  function renderDenominations() {
    denomContainer.innerHTML = "";
    denomValues.forEach(v => {
      const box = document.createElement("div");
      box.className = "denom";
      box.innerHTML = `
        <label>₹${v}: <input type="number" class="denom-count" data-value="${v}" value="0" min="0" style="width:72px" /></label>
      `;
      denomContainer.appendChild(box);
    });
  }

  addItemBtn.addEventListener("click", (ev) => {
    ev.preventDefault();
    addProductRow();
  });

  generateBtn.addEventListener("click", async (ev) => {
  ev.preventDefault();
  ev.stopPropagation();

  // Clear previous inline error highlights/messages
  resultEl.innerHTML = "";
  document.querySelectorAll(".input-error").forEach(el => el.classList.remove("input-error"));
  document.querySelectorAll(".field-error-msg").forEach(el => el.remove());

  const email = document.getElementById("customer_email").value.trim();
  const paid_value = document.getElementById("paid_amount").value;
  const items = [];
  const errors = [];

  if (!email) {
    errors.push("Customer email is required.");
  } else {
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(email)) errors.push("Enter a valid email address.");
  }

  document.querySelectorAll(".items-row").forEach((r, idx) => {
    const codeEl = r.querySelector(".product-code");
    const qtyEl = r.querySelector(".product-qty");
    const code = (codeEl && codeEl.value || "").trim();
    const qty = parseInt(qtyEl && qtyEl.value || "0");

    r.querySelectorAll(".field-error-msg").forEach(el => el.remove());
    if (!code) {
      const msg = document.createElement("div");
      msg.className = "field-error-msg";
      msg.style.color = "red";
      msg.style.fontSize = "12px";
      msg.style.marginTop = "6px";
      msg.textContent = "Product ID required";
      r.appendChild(msg);
      if (codeEl) codeEl.classList.add("input-error");
      errors.push(`Product row ${idx + 1}: product ID required.`);
    }
    if (!qty || qty <= 0) {
      const msg = document.createElement("div");
      msg.className = "field-error-msg";
      msg.style.color = "red";
      msg.style.fontSize = "12px";
      msg.style.marginTop = "6px";
      msg.textContent = "Quantity must be at least 1";
      r.appendChild(msg);
      if (qtyEl) qtyEl.classList.add("input-error");
      errors.push(`Product row ${idx + 1}: quantity must be at least 1.`);
    }

    if (code && qty > 0) items.push({ product_code: code, quantity: qty });
  });

  if (items.length === 0) {
    errors.push("Add at least one valid product.");
  }

  const paidFloat = parseFloat(paid_value || 0);
  if (isNaN(paidFloat) || paidFloat < 0) {
    errors.push("Paid amount must be a valid number (>= 0).");
    const paidEl = document.getElementById("paid_amount");
    if (paidEl) paidEl.classList.add("input-error");
  }

  if (errors.length > 0) {
    const ul = document.createElement("ul");
    ul.style.background = "#ffecec";
    ul.style.border = "1px solid #f5c2c2";
    ul.style.color = "#c00";
    ul.style.padding = "10px";
    ul.style.borderRadius = "6px";
    ul.style.listStyle = "disc";
    ul.style.margin = "0 0 12px 0";
    errors.forEach(err => {
      const li = document.createElement("li");
      li.textContent = err;
      ul.appendChild(li);
    });
    resultEl.innerHTML = "";
    resultEl.appendChild(ul);
    return;
  }

  const denoms = [];
  document.querySelectorAll(".denom-count").forEach(el => {
    denoms.push({ value: parseInt(el.dataset.value), count: parseInt(el.value || "0") });
  });

  const body = {
    customer_email: email,
    items: items,
    denominations: denoms,
    paid_amount: parseFloat(paidFloat.toFixed(2))
  };

  try {
    resultEl.textContent = "Processing...";
    const res = await fetch("/api/generate-bill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    console.log("API /api/generate-bill response:", res.status, data);

    if (!res.ok) {
      const msg = data.detail || JSON.stringify(data);
      resultEl.innerHTML = `<div style="background:#ffecec;border:1px solid #f5c2c2;color:#c00;padding:10px;border-radius:6px;">Error: ${msg}</div>`;
      return;
    }

    const emailParam = encodeURIComponent(data.customer_email || email);
    window.location.href = `/preview/${data.bill_id}?email=${emailParam}`;
  } catch (err) {
    resultEl.innerHTML = `<div style="background:#ffecec;border:1px solid #f5c2c2;color:#c00;padding:10px;border-radius:6px;">Network error: ${err.message}</div>`;
  }
});

  viewPurchases.addEventListener("click", (e) => {
        e.preventDefault();
        const email = document.getElementById("customer_email").value;
        if (!email) {
        alert("Enter customer email to view purchases.");
        return;
        }
        window.location.href = `/purchases?email=${encodeURIComponent(email)}`;
    });

  renderDenominations();
  addProductRow(); 
});