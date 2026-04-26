function makeExpenseRow(){
  const rowId = 'expense-row-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  const today = new Date().toISOString().slice(0,10);
  
  // Desktop table row
  const tr = document.createElement("tr");
  tr.id = rowId;
  tr.innerHTML = `
    <td class="px-4 py-3">
      <input type="date" class="w-full px-3 py-2 border rounded-lg text-sm js-date" value="${today}">
    </td>
    <td class="px-4 py-3">
      <select class="w-full px-3 py-2 border rounded-lg text-sm js-category"></select>
    </td>
    <td class="px-4 py-3">
      <input type="text" class="w-full px-3 py-2 border rounded-lg text-sm js-desc" placeholder="e.g. bubble wrap, ads, electricity">
    </td>
    <td class="px-4 py-3">
      <input type="number" inputmode="decimal" class="w-full px-3 py-2 border rounded-lg text-sm text-right js-amount" placeholder="0.00">
    </td>
    <td class="px-4 py-3 no-print text-right">
      <button class="p-2 text-red-500 hover:bg-red-50 rounded-lg js-del" type="button" title="Remove row">
        <i class="fa-solid fa-trash"></i>
      </button>
    </td>
  `;

  // Mobile card
  const card = document.createElement("div");
  card.className = "bg-white rounded-xl shadow-sm border p-4";
  card.id = "expense-card-" + rowId;
  card.innerHTML = `
    <div class="flex items-start justify-between mb-3">
      <span class="font-medium text-gray-800 js-category-badge">Packaging</span>
      <button class="p-2 text-red-500 hover:bg-red-50 rounded-lg js-del" type="button">
        <i class="fa-solid fa-trash"></i>
      </button>
    </div>
    <div class="space-y-3">
      <div>
        <label class="block text-xs text-gray-500 mb-1">Date</label>
        <input type="date" class="w-full px-3 py-2.5 border rounded-lg text-sm js-date" value="${today}">
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">Category</label>
        <select class="w-full px-3 py-2.5 border rounded-lg text-sm js-category"></select>
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">Description</label>
        <input type="text" class="w-full px-3 py-2.5 border rounded-lg text-sm js-desc" placeholder="e.g. bubble wrap, ads, electricity">
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">Amount (₱)</label>
        <input type="number" inputmode="decimal" class="w-full px-3 py-2.5 border rounded-lg text-sm js-amount" placeholder="0.00">
      </div>
    </div>
  `;

  const sel = tr.querySelector(".js-category");
  const cardSel = card.querySelector(".js-category");
  (window.APP_EXPENSE_CATEGORIES || []).forEach(c => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
    cardSel.appendChild(opt.cloneNode(true));
  });
  sel.value = "Packaging";
  cardSel.value = "Packaging";

  function updateCategoryBadge() {
    const category = sel.value;
    card.querySelector(".js-category-badge").textContent = category;
  }

  sel.addEventListener("change", () => { 
    cardSel.value = sel.value;
    updateCategoryBadge();
  });
  cardSel.addEventListener("change", () => { 
    sel.value = cardSel.value;
    updateCategoryBadge();
  });

  const amountInput = tr.querySelector(".js-amount");
  const cardAmountInput = card.querySelector(".js-amount");
  amountInput.addEventListener("input", () => { 
    cardAmountInput.value = amountInput.value;
    recalcExpenseRow(tr, card); 
    recalcExpenseTotals(); 
  });
  cardAmountInput.addEventListener("input", () => { 
    amountInput.value = cardAmountInput.value;
    recalcExpenseRow(tr, card); 
    recalcExpenseTotals(); 
  });

  const dateInput = tr.querySelector(".js-date");
  const cardDateInput = card.querySelector(".js-date");
  dateInput.addEventListener("input", () => { cardDateInput.value = dateInput.value; });
  cardDateInput.addEventListener("input", () => { dateInput.value = cardDateInput.value; });

  const descInput = tr.querySelector(".js-desc");
  const cardDescInput = card.querySelector(".js-desc");
  descInput.addEventListener("input", () => { cardDescInput.value = descInput.value; });
  cardDescInput.addEventListener("input", () => { descInput.value = cardDescInput.value; });

  const delBtn = tr.querySelector(".js-del");
  const cardDelBtn = card.querySelector(".js-del");
  delBtn.addEventListener("click", () => { 
    tr.remove(); 
    card.remove(); 
    recalcExpenseTotals(); 
  });
  cardDelBtn.addEventListener("click", () => { 
    tr.remove(); 
    card.remove(); 
    recalcExpenseTotals(); 
  });

  updateCategoryBadge();
  
  document.getElementById("expenseTbody").appendChild(tr);
  document.getElementById("expenseCardContainer").appendChild(card);
  
  return { tr, card };
}

function recalcExpenseRow(tr, card){
  const amt = Math.max(0, Number(tr.querySelector(".js-amount").value || 0));
  tr.dataset.amount = String(+amt.toFixed(2));
}

function recalcExpenseTotals(){
  const rows = Array.from(document.querySelectorAll("#expenseTbody tr"));
  const total = rows.reduce((a,r)=>a+(+r.dataset.amount||0),0);
  document.getElementById("tExp").textContent = `₱ ${(+total.toFixed(2)).toFixed(2)}`;
}

function collectExpenseRows(){
  const trs = Array.from(document.querySelectorAll("#expenseTbody tr"));
  return trs.map(tr => ({
    date: tr.querySelector(".js-date").value,
    category: tr.querySelector(".js-category").value,
    description: tr.querySelector(".js-desc").value.trim(),
    amount: Number(tr.querySelector(".js-amount").value || 0),
  })).filter(r => r.amount > 0 || r.description || r.date);
}

function showExpenseToast(message, type = "info") {
  const toastArea = document.getElementById("toastArea");
  const toast = document.createElement("div");
  const bgColor = type === "success" ? "bg-green-500" : type === "error" ? "bg-red-500" : "bg-indigo-500";
  toast.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-pulse`;
  toast.innerHTML = `
    <i class="fa-solid fa-${type === "success" ? "check-circle" : type === "error" ? "exclamation-circle" : "info-circle"}"></i>
    <span>${message}</span>
  `;
  toastArea.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

async function syncExpenses(){
  const btn = document.getElementById("syncExpensesBtn");
  btn.disabled = true;
  btn.querySelector(".sync-label").classList.add("hidden");
  btn.querySelector(".sync-spinner").classList.remove("hidden");
  try{
    const rows = collectExpenseRows();
    const resp = await fetch("/api/expenses/bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows }),
    });
    const data = await resp.json().catch(()=>({}));
    if(!resp.ok || !data.ok){
      const extra = data?.gas?.json?.message || data?.gas?.text;
      throw new Error([data.error || `Sync failed (${resp.status})`, extra].filter(Boolean).join(" — "));
    }
    const okMsg = data?.gas?.json?.message || data?.gas?.json?.result || null;
    showExpenseToast(okMsg ? `${data.count} row(s) synced. ${okMsg}` : `${data.count} row(s) synced successfully.`, "success");
  }catch(e){
    showExpenseToast(String(e?.message || e), "error");
  }finally{
    btn.disabled = false;
    btn.querySelector(".sync-label").classList.remove("hidden");
    btn.querySelector(".sync-spinner").classList.add("hidden");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const add = () => {
    const { tr, card } = makeExpenseRow();
    recalcExpenseRow(tr, card);
    recalcExpenseTotals();
  };
  document.getElementById("addExpenseRowBtn").addEventListener("click", add);
  document.getElementById("syncExpensesBtn").addEventListener("click", syncExpenses);
  for(let i=0;i<10;i++) add();
});

