function money(n){
  const x = Number(n || 0);
  return x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function showToast({ title = "Done", message = "", variant = "success" }){
  const area = document.getElementById("toastArea");
  if(!area) return;

  const colors = {
    success: "bg-green-600",
    danger: "bg-red-600",
    warning: "bg-amber-500",
    info: "bg-blue-600"
  };
  const colorClass = colors[variant] || colors.success;

  const el = document.createElement("div");
  el.className = `${colorClass} text-white px-4 py-3 rounded-lg shadow-lg flex items-center justify-between gap-4 min-w-[280px] animate-fade-in-down`;
  el.setAttribute("role", "status");
  el.setAttribute("aria-live", "polite");
  el.innerHTML = `
    <div>
      <div class="font-semibold">${title}</div>
      <div class="text-sm opacity-90">${message}</div>
    </div>
    <button type="button" class="text-white hover:text-gray-200 transition" onclick="this.parentElement.remove()" aria-label="Close">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;
  area.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

window.LedgerUI = { money, showToast };

