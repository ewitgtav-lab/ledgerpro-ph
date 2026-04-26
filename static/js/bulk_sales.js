function platformIcon(platform){
  const p = (platform || "").toLowerCase();
  if(p === "shopee") return `<i class="fa-brands fa-shopify text-indigo-600"></i>`;
  if(p === "tiktok") return `<i class="fa-brands fa-tiktok text-pink-600"></i>`;
  if(p === "lazada") return `<i class="fa-solid fa-store text-blue-600"></i>`;
  return `<i class="fa-regular fa-circle text-gray-400"></i>`;
}

function platformBadge(platform) {
  const p = (platform || "").toLowerCase();
  if(p === "shopee") return `<span class="inline-flex items-center gap-1 bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full text-xs font-medium"><i class="fa-brands fa-shopify"></i> Shopee</span>`;
  if(p === "tiktok") return `<span class="inline-flex items-center gap-1 bg-pink-100 text-pink-700 px-2 py-1 rounded-full text-xs font-medium"><i class="fa-brands fa-tiktok"></i> TikTok</span>`;
  if(p === "lazada") return `<span class="inline-flex items-center gap-1 bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs font-medium"><i class="fa-solid fa-store"></i> Lazada</span>`;
  return `<span class="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">${platform}</span>`;
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
  const rowId = 'row-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  const today = new Date().toISOString().slice(0,10);
  
  // Desktop table row
  const tr = document.createElement("tr");
  tr.id = rowId;
  tr.innerHTML = `
    <td class="px-4 py-3">
      <input type="date" class="w-full px-3 py-2 border rounded-lg text-sm js-date" value="${today}">
    </td>
    <td class="px-4 py-3">
      <div class="flex items-center gap-2">
        <span class="js-platform-icon">${platformIcon("Shopee")}</span>
        <select class="flex-1 px-3 py-2 border rounded-lg text-sm js-platform"></select>
      </div>
    </td>
    <td class="px-4 py-3">
      <input type="text" class="w-full px-3 py-2 border rounded-lg text-sm js-order" placeholder="e.g. SPX-123...">
    </td>
    <td class="px-4 py-3">
      <input type="number" inputmode="decimal" class="w-full px-3 py-2 border rounded-lg text-sm text-right js-gross" placeholder="0.00">
    </td>
    <td class="px-4 py-3 text-right text-sm text-gray-600"><span class="js-fee">₱ 0.00</span></td>
    <td class="px-4 py-3 text-right text-sm text-gray-600"><span class="js-wht">₱ 0.00</span></td>
    <td class="px-4 py-3 text-right text-sm text-gray-600"><span class="js-bir8">₱ 0.00</span></td>
    <td class="px-4 py-3 text-right text-sm font-semibold text-green-600"><span class="js-net">₱ 0.00</span></td>
    <td class="px-4 py-3 no-print text-right">
      <button class="p-2 text-red-500 hover:bg-red-50 rounded-lg js-del" type="button" title="Remove row">
        <i class="fa-solid fa-trash"></i>
      </button>
    </td>
  `;

  // Mobile card
  const card = document.createElement("div");
  card.className = "bg-white rounded-xl shadow-sm border p-4";
  card.id = "card-" + rowId;
  card.innerHTML = `
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="js-platform-icon">${platformIcon("Shopee")}</span>
        <span class="font-medium text-gray-800 js-platform-badge">${platformBadge("Shopee")}</span>
      </div>
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
        <label class="block text-xs text-gray-500 mb-1">Platform</label>
        <select class="w-full px-3 py-2.5 border rounded-lg text-sm js-platform"></select>
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">Order ID</label>
        <input type="text" class="w-full px-3 py-2.5 border rounded-lg text-sm js-order" placeholder="e.g. SPX-123...">
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">Gross Amount (₱)</label>
        <input type="number" inputmode="decimal" class="w-full px-3 py-2.5 border rounded-lg text-sm js-gross" placeholder="0.00">
      </div>
      <div class="bg-gray-50 rounded-lg p-3 space-y-2">
        <div class="flex justify-between text-sm">
          <span class="text-gray-500">Platform Fee</span>
          <span class="js-fee font-medium">₱ 0.00</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-500">WHT 1%</span>
          <span class="js-wht font-medium">₱ 0.00</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-500">BIR 8%</span>
          <span class="js-bir8 font-medium">₱ 0.00</span>
        </div>
        <div class="border-t pt-2 flex justify-between">
          <span class="text-gray-700 font-semibold">Net Profit</span>
          <span class="js-net font-bold text-green-600">₱ 0.00</span>
        </div>
      </div>
    </div>
  `;

  const sel = tr.querySelector(".js-platform");
  const cardSel = card.querySelector(".js-platform");
  (window.APP_PLATFORMS || ["Shopee","Lazada","TikTok"]).forEach(p => {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p;
    sel.appendChild(opt);
    cardSel.appendChild(opt.cloneNode(true));
  });

  function updateIcons(){
    const platform = sel.value;
    tr.querySelector(".js-platform-icon").innerHTML = platformIcon(platform);
    card.querySelector(".js-platform-icon").innerHTML = platformIcon(platform);
    card.querySelector(".js-platform-badge").innerHTML = platformBadge(platform);
  }
  
  sel.addEventListener("change", () => { 
    cardSel.value = sel.value;
    updateIcons(); 
    recalcRow(tr, card); 
    recalcTotals(); 
  });
  
  cardSel.addEventListener("change", () => { 
    sel.value = cardSel.value;
    updateIcons(); 
    recalcRow(tr, card); 
    recalcTotals(); 
  });

  const grossInput = tr.querySelector(".js-gross");
  const cardGrossInput = card.querySelector(".js-gross");
  grossInput.addEventListener("input", () => { 
    cardGrossInput.value = grossInput.value;
    recalcRow(tr, card); 
    recalcTotals(); 
  });
  cardGrossInput.addEventListener("input", () => { 
    grossInput.value = cardGrossInput.value;
    recalcRow(tr, card); 
    recalcTotals(); 
  });

  const dateInput = tr.querySelector(".js-date");
  const cardDateInput = card.querySelector(".js-date");
  dateInput.addEventListener("input", () => { cardDateInput.value = dateInput.value; });
  cardDateInput.addEventListener("input", () => { dateInput.value = cardDateInput.value; });

  const orderInput = tr.querySelector(".js-order");
  const cardOrderInput = card.querySelector(".js-order");
  orderInput.addEventListener("input", () => { cardOrderInput.value = orderInput.value; });
  cardOrderInput.addEventListener("input", () => { orderInput.value = cardOrderInput.value; });

  const delBtn = tr.querySelector(".js-del");
  const cardDelBtn = card.querySelector(".js-del");
  delBtn.addEventListener("click", () => { 
    tr.remove(); 
    card.remove(); 
    recalcTotals(); 
  });
  cardDelBtn.addEventListener("click", () => { 
    tr.remove(); 
    card.remove(); 
    recalcTotals(); 
  });

  updateIcons();
  
  // Add to containers
  document.getElementById("bulkTbody").appendChild(tr);
  document.getElementById("cardContainer").appendChild(card);
  
  return { tr, card };
}

function recalcRow(tr, card){
  const platform = tr.querySelector(".js-platform").value;
  const gross = tr.querySelector(".js-gross").value;
  const { fee, wht, bir8, net } = computeRow(platform, gross);

  tr.dataset.gross = String(Math.max(0, Number(gross || 0)));
  tr.dataset.fee = String(fee);
  tr.dataset.bir8 = String(bir8);
  tr.dataset.net = String(net);

  tr.querySelector(".js-fee").textContent = `₱ ${fee.toFixed(2)}`;
  tr.querySelector(".js-wht").textContent = `₱ ${wht.toFixed(2)}`;
  tr.querySelector(".js-bir8").textContent = `₱ ${bir8.toFixed(2)}`;
  tr.querySelector(".js-net").textContent = `₱ ${net.toFixed(2)}`;

  if (card) {
    card.querySelector(".js-fee").textContent = `₱ ${fee.toFixed(2)}`;
    card.querySelector(".js-wht").textContent = `₱ ${wht.toFixed(2)}`;
    card.querySelector(".js-bir8").textContent = `₱ ${bir8.toFixed(2)}`;
    card.querySelector(".js-net").textContent = `₱ ${net.toFixed(2)}`;
  }
}

function recalcTotals(){
  const rows = Array.from(document.querySelectorAll("#bulkTbody tr"));
  const sum = (key) => rows.reduce((a,r)=>a+(+r.dataset[key]||0),0);
  const gross = +sum("gross").toFixed(2);
  const fees = +sum("fee").toFixed(2);
  const bir8 = +sum("bir8").toFixed(2);
  const net = +sum("net").toFixed(2);
  document.getElementById("tGross").textContent = `₱ ${gross.toFixed(2)}`;
  document.getElementById("tFees").textContent = `₱ ${fees.toFixed(2)}`;
  document.getElementById("tBir8").textContent = `₱ ${bir8.toFixed(2)}`;
  document.getElementById("tNet").textContent = `₱ ${net.toFixed(2)}`;
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
  btn.querySelector(".sync-label").classList.add("hidden");
  btn.querySelector(".sync-spinner").classList.remove("hidden");
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
    showToast(okMsg ? `${data.count} row(s) synced. ${okMsg}` : `${data.count} row(s) synced successfully.`, "success");
  }catch(e){
    showToast(String(e?.message || e), "error");
  }finally{
    btn.disabled = false;
    btn.querySelector(".sync-label").classList.remove("hidden");
    btn.querySelector(".sync-spinner").classList.add("hidden");
  }
}

function showToast(message, type = "info") {
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

document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("bulkTbody");
  const cardContainer = document.getElementById("cardContainer");
  const add = () => {
    const { tr, card } = makeRow();
    recalcRow(tr, card);
    recalcTotals();
  };
  document.getElementById("addRowBtn").addEventListener("click", add);
  document.getElementById("bulkSyncBtn").addEventListener("click", bulkSync);

  // start with 10 rows
  for(let i=0;i<10;i++) add();
});

