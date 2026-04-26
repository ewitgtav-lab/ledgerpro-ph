function setText(id, value){
  const el = document.getElementById(id);
  if(el) el.textContent = value || "—";
}

function amountToWordsPHP(value){
  const n = Math.max(0, Number(value || 0));
  if(!isFinite(n)) return "";
  if(n === 0) return "ZERO PESOS ONLY";

  const ones = ["","ONE","TWO","THREE","FOUR","FIVE","SIX","SEVEN","EIGHT","NINE","TEN","ELEVEN","TWELVE","THIRTEEN","FOURTEEN","FIFTEEN","SIXTEEN","SEVENTEEN","EIGHTEEN","NINETEEN"];
  const tens = ["","","TWENTY","THIRTY","FORTY","FIFTY","SIXTY","SEVENTY","EIGHTY","NINETY"];
  const chunk = (num) => {
    let out = [];
    if(num >= 100){
      out.push(ones[Math.floor(num/100)], "HUNDRED");
      num = num % 100;
    }
    if(num >= 20){
      out.push(tens[Math.floor(num/10)]);
      num = num % 10;
      if(num) out.push(ones[num]);
    }else if(num > 0){
      out.push(ones[num]);
    }
    return out.filter(Boolean).join(" ");
  };
  const parts = [];
  let whole = Math.floor(n);
  const cents = Math.round((n - whole) * 100);

  const scales = [
    { v: 1_000_000_000, s: "BILLION" },
    { v: 1_000_000, s: "MILLION" },
    { v: 1_000, s: "THOUSAND" },
  ];
  for(const sc of scales){
    if(whole >= sc.v){
      const q = Math.floor(whole / sc.v);
      parts.push(chunk(q), sc.s);
      whole = whole % sc.v;
    }
  }
  if(whole) parts.push(chunk(whole));

  let words = `${parts.join(" ")} PESOS`;
  if(cents){
    words += ` AND ${chunk(cents)} CENTAVOS`;
  }
  return `${words} ONLY`.replace(/\s+/g," ").trim();
}

document.addEventListener("DOMContentLoaded", () => {
  const today = new Date().toISOString().slice(0,10);
  const rDate = document.getElementById("rDate");
  if(rDate && !rDate.value) rDate.value = today;

  const bind = (inputId, paperId, formatter) => {
    const inp = document.getElementById(inputId);
    if(!inp) return;
    const update = () => {
      const val = formatter ? formatter(inp.value) : inp.value;
      setText(paperId, val);
    };
    inp.addEventListener("input", update);
    inp.addEventListener("change", update);
    update();
  };

  bind("rRef", "pRef");
  bind("rFrom", "pFrom");
  bind("rFor", "pFor");
  bind("rBy", "pBy");
  bind("rDate", "pDate");
  bind("rAmount", "pAmount", (v) => window.LedgerUI.money(v));
  bind("rAmount", "pAmountWords", (v) => amountToWordsPHP(v));

  const resetBtn = document.getElementById("resetReceiptBtn");
  if(resetBtn){
    resetBtn.addEventListener("click", () => {
      ["rRef","rFrom","rAmount","rFor","rBy"].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.value = "";
      });
      if(rDate) rDate.value = today;
      ["pRef","pFrom","pFor","pBy"].forEach(id => setText(id, "—"));
      setText("pAmount", "0.00");
      setText("pAmountWords", "—");
      setText("pDate", today);
    });
  }
});

