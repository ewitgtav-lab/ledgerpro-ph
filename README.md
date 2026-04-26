# LedgerPro PH (Flask)

Professional **E‑Commerce Tax & Ledger System** starter for Philippine Shopee, Lazada, and TikTok Shop sellers.

## Run locally (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Optional: set your Google Apps Script Web App URL
$env:GAS_WEBAPP_URL="https://script.google.com/macros/s/XXXX/exec"

.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000`

## Pages

- `/` Dashboard (stat cards)
- `/sales-journal` Bulk entry table + Bulk Sync (spinner + toast)
- `/receipt` Printable Acknowledgement Receipt (Print/Save as PDF)

## Google Apps Script payload

The app POSTs:

```json
{ "rows": [ { "date": "YYYY-MM-DD", "platform": "Shopee|Lazada|TikTok", "order_id": "...", "gross_amount": 123.45, "platform_fee": 0, "withholding_1pct": 0, "bir_8pct": 0, "net_profit": 0 } ] }
```

