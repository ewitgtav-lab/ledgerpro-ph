function makeExpenseRow(){
  const tr = document.createElement("tr");
  const today = new Date().toISOString().slice(0,10);
  tr.innerHTML = `
    <td class="nowrap">
      <input type="date" class="form-control form-control-sm js-date" value="${today}">
    </td>
    <td style="min-width: 200px;">
      <select class="form-select form-select-sm js-category"></select>
    </td>
    <td style="min-width: 220px;">
      <input type="text" class="form-control form-control-sm js-desc" placeholder="e.g. bubble wrap, ads, electricity">
    </td>
    <td style="min-width: 140px;">
      <input inputmode="decimal" class="form-control form-control-sm text-end js-amount" placeholder="0.00">
    </td>
    <td class="no-print text-end">
      <button class="btn btn-sm btn-outline-danger js-del" type="button" title="Remove row">
        <i class="fa-solid fa-trash"></i>
      </button>
    </td>
  `;

  const sel = tr.querySelector(".js-category");
  (window.APP_EXPENSE_CATEGORIES || []).forEach(c => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });

  tr.querySelector(".js-amount").addEventListener("input", () => { recalcExpenseRow(tr); recalcExpenseTotals(); });
  tr.querySelector(".js-del").addEventListener("click", () => { tr.remove(); recalcExpenseTotals(); });

  return tr;
}

function recalcExpenseRow(tr){
  const amt = Math.max(0, Number(tr.querySelector(".js-amount").value || 0));
  tr.dataset.amount = String(+amt.toFixed(2));
}

function recalcExpenseTotals(){
  const rows = Array.from(document.querySelectorAll("#expenseTbody tr"));
  const total = rows.reduce((a,r)=>a+(+r.dataset.amount||0),0);
  document.getElementById("tExp").textContent = `₱ ${window.LedgerUI.money(+total.toFixed(2))}`;
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

async function syncExpenses(){
  const btn = document.getElementById("syncExpensesBtn");
  btn.disabled = true;
  btn.querySelector(".sync-label").classList.add("d-none");
  btn.querySelector(".sync-spinner").classList.remove("d-none");
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
    window.LedgerUI.showToast({
      title: "Expenses synced",
      message: okMsg ? `${data.count} row(s) synced. ${okMsg}` : `${data.count} row(s) synced successfully.`,
      variant: "success",
    });
  }catch(e){
    window.LedgerUI.showToast({
      title: "Sync failed",
      message: String(e?.message || e),
      variant: "danger",
    });
  }finally{
    btn.disabled = false;
    btn.querySelector(".sync-label").classList.remove("d-none");
    btn.querySelector(".sync-spinner").classList.add("d-none");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("expenseTbody");
  const add = () => {
    const tr = makeExpenseRow();
    tbody.appendChild(tr);
    recalcExpenseRow(tr);
    recalcExpenseTotals();
  };
  document.getElementById("addExpenseRowBtn").addEventListener("click", add);
  document.getElementById("syncExpensesBtn").addEventListener("click", syncExpenses);
  for(let i=0;i<10;i++) add();
});

