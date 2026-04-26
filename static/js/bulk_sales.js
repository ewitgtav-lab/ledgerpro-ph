function platformIcon(platform){
  const p = (platform || "").toLowerCase();
  if(p === "shopee") return `<i class="fa-brands fa-shopify me-2 text-muted"></i>`;
  if(p === "tiktok") return `<i class="fa-brands fa-tiktok me-2 text-muted"></i>`;
  if(p === "lazada") return `<i class="fa-solid fa-store me-2 text-muted"></i>`;
  return `<i class="fa-regular fa-circle me-2 text-muted"></i>`;
}

function estimatePlatformFee(platform, gross){
  const g = Math.max(0, Number(gross || 0));
  const rates = { Shopee: 0.060, Lazada: 0.055, TikTok: 0.050 };
  const r = rates[platform] ?? 0;
  return +(g * r).toFixed(2);
}

function computeRow(platform, gross){
  const g = Math.max(0, Number(gross || 0));
  const fee = estimatePlatformFee(platform, g);
  const wht = +(g * 0.01).toFixed(2);
  const bir8Base = Math.max(0, g - fee);
  const bir8 = +(bir8Base * 0.08).toFixed(2);
  const net = +(g - fee - wht - bir8).toFixed(2);
  return { fee, wht, bir8, net };
}

function makeRow(){
  const tr = document.createElement("tr");
  const today = new Date().toISOString().slice(0,10);
  tr.innerHTML = `
    <td class="nowrap">
      <input type="date" class="form-control form-control-sm js-date" value="${today}">
    </td>
    <td style="min-width: 160px;">
      <div class="input-group input-group-sm">
        <span class="input-group-text bg-white">${platformIcon("Shopee")}</span>
        <select class="form-select js-platform"></select>
      </div>
    </td>
    <td style="min-width: 160px;">
      <input type="text" class="form-control form-control-sm js-order" placeholder="e.g. SPX-123...">
    </td>
    <td style="min-width: 140px;">
      <input inputmode="decimal" class="form-control form-control-sm text-end js-gross" placeholder="0.00">
    </td>
    <td class="text-end nowrap small"><span class="js-fee">₱ 0.00</span></td>
    <td class="text-end nowrap small"><span class="js-wht">₱ 0.00</span></td>
    <td class="text-end nowrap small"><span class="js-bir8">₱ 0.00</span></td>
    <td class="text-end nowrap small fw-semibold"><span class="js-net">₱ 0.00</span></td>
    <td class="no-print text-end">
      <button class="btn btn-sm btn-outline-danger js-del" type="button" title="Remove row">
        <i class="fa-solid fa-trash"></i>
      </button>
    </td>
  `;

  const sel = tr.querySelector(".js-platform");
  (window.APP_PLATFORMS || ["Shopee","Lazada","TikTok"]).forEach(p => {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p;
    sel.appendChild(opt);
  });

  function updateIcon(){
    const iconEl = tr.querySelector(".input-group-text");
    iconEl.innerHTML = platformIcon(sel.value);
  }
  sel.addEventListener("change", () => { updateIcon(); recalcRow(tr); recalcTotals(); });

  tr.querySelector(".js-gross").addEventListener("input", () => { recalcRow(tr); recalcTotals(); });
  tr.querySelector(".js-del").addEventListener("click", () => { tr.remove(); recalcTotals(); });

  updateIcon();
  return tr;
}

function recalcRow(tr){
  const platform = tr.querySelector(".js-platform").value;
  const gross = tr.querySelector(".js-gross").value;
  const { fee, wht, bir8, net } = computeRow(platform, gross);

  tr.dataset.gross = String(Math.max(0, Number(gross || 0)));
  tr.dataset.fee = String(fee);
  tr.dataset.bir8 = String(bir8);
  tr.dataset.net = String(net);

  tr.querySelector(".js-fee").textContent = `₱ ${window.LedgerUI.money(fee)}`;
  tr.querySelector(".js-wht").textContent = `₱ ${window.LedgerUI.money(wht)}`;
  tr.querySelector(".js-bir8").textContent = `₱ ${window.LedgerUI.money(bir8)}`;
  tr.querySelector(".js-net").textContent = `₱ ${window.LedgerUI.money(net)}`;
}

function recalcTotals(){
  const rows = Array.from(document.querySelectorAll("#bulkTbody tr"));
  const sum = (key) => rows.reduce((a,r)=>a+(+r.dataset[key]||0),0);
  const gross = +sum("gross").toFixed(2);
  const fees = +sum("fee").toFixed(2);
  const bir8 = +sum("bir8").toFixed(2);
  const net = +sum("net").toFixed(2);
  document.getElementById("tGross").textContent = `₱ ${window.LedgerUI.money(gross)}`;
  document.getElementById("tFees").textContent = `₱ ${window.LedgerUI.money(fees)}`;
  document.getElementById("tBir8").textContent = `₱ ${window.LedgerUI.money(bir8)}`;
  document.getElementById("tNet").textContent = `₱ ${window.LedgerUI.money(net)}`;
}

function collectRows(){
  const trs = Array.from(document.querySelectorAll("#bulkTbody tr"));
  return trs.map(tr => ({
    date: tr.querySelector(".js-date").value,
    platform: tr.querySelector(".js-platform").value,
    order_id: tr.querySelector(".js-order").value.trim(),
    gross_amount: Number(tr.querySelector(".js-gross").value || 0),
  })).filter(r => r.gross_amount > 0 || r.order_id || r.date);
}

async function bulkSync(){
  const btn = document.getElementById("bulkSyncBtn");
  btn.disabled = true;
  btn.querySelector(".sync-label").classList.add("d-none");
  btn.querySelector(".sync-spinner").classList.remove("d-none");
  try{
    const rows = collectRows();
    const resp = await fetch("/api/sales/bulk", {
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
      title: "Synced to Google Sheet",
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
  const tbody = document.getElementById("bulkTbody");
  const add = () => {
    const tr = makeRow();
    tbody.appendChild(tr);
    recalcRow(tr);
    recalcTotals();
  };
  document.getElementById("addRowBtn").addEventListener("click", add);
  document.getElementById("bulkSyncBtn").addEventListener("click", bulkSync);

  // start with 10 rows
  for(let i=0;i<10;i++) add();
});

