from __future__ import annotations

import os
from collections import defaultdict
from datetime import date
from typing import Any

import requests
from flask import Flask, jsonify, redirect, render_template, request, url_for

from accounting import PLATFORMS, compute_taxes_and_net, parse_iso_date


def create_app() -> Flask:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # Optional dependency in some deployments; env vars still work.
        pass

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    app.config["GOOGLE_SCRIPT_URL"] = (
        os.environ.get("GOOGLE_SCRIPT_URL") or os.environ.get("GAS_WEBAPP_URL") or ""
    ).strip()

    # In-memory store for now (easy to swap to DB later)
    app.config["TXNS"]: list[dict[str, Any]] = []
    app.config["EXPENSES"]: list[dict[str, Any]] = []

    @app.get("/")
    def dashboard():
        txns = app.config["TXNS"]
        total_gross = round(sum(t["gross_amount"] for t in txns), 2)
        total_fees = round(sum(t["platform_fee"] for t in txns), 2)
        est_8pct = round(sum(t["bir_8pct"] for t in txns), 2)
        net_profit = round(sum(t["net_profit"] for t in txns), 2)
        return render_template(
            "dashboard.html",
            total_gross=total_gross,
            total_fees=total_fees,
            est_8pct=est_8pct,
            net_profit=net_profit,
            platforms=PLATFORMS,
        )

    @app.get("/sales-journal")
    def sales_journal():
        return render_template("sales_journal.html", platforms=PLATFORMS)

    @app.get("/expense-journal")
    def expense_journal():
        categories = ["Packaging", "Shipping Fees", "Marketing/Ads", "Utilities", "Inventory", "Others"]
        return render_template("expense_journal.html", categories=categories)

    @app.get("/reports")
    def reports():
        txns = app.config["TXNS"]
        expenses = app.config["EXPENSES"]

        by_month: dict[str, dict[str, float]] = defaultdict(lambda: {
            "gross_sales": 0.0,
            "platform_fees": 0.0,
            "wht_1pct": 0.0,
            "expenses": 0.0,
        })

        for t in txns:
            m = str(t.get("date", ""))[:7] or "Unknown"
            by_month[m]["gross_sales"] += float(t.get("gross_amount") or 0.0)
            by_month[m]["platform_fees"] += float(t.get("platform_fee") or 0.0)
            by_month[m]["wht_1pct"] += float(t.get("withholding_1pct") or 0.0)

        for e in expenses:
            m = str(e.get("date", ""))[:7] or "Unknown"
            by_month[m]["expenses"] += float(e.get("amount") or 0.0)

        rows: list[dict[str, Any]] = []
        for month in sorted(by_month.keys()):
            s = by_month[month]
            gross = round(s["gross_sales"], 2)
            fees = round(s["platform_fees"], 2)
            exp = round(s["expenses"], 2)
            net_taxable = round(max(0.0, gross - exp), 2)

            bir8_base = max(0.0, gross - fees - exp)
            bir8_due = round(bir8_base * 0.08, 2)
            wht = round(s["wht_1pct"], 2)
            final_tax = round(max(0.0, bir8_due - wht), 2)

            rows.append(
                {
                    "month": month,
                    "gross_sales": gross,
                    "expenses": exp,
                    "net_taxable_income": net_taxable,
                    "bir_8pct_due": bir8_due,
                    "wht_credit": wht,
                    "final_tax_payable": final_tax,
                }
            )

        return render_template("reports.html", rows=rows)

    @app.get("/receipt")
    def receipt():
        return render_template("receipt.html")

    @app.post("/api/compute")
    def api_compute():
        payload = request.get_json(silent=True) or {}
        platform = payload.get("platform", "")
        gross = float(payload.get("gross_amount") or 0.0)
        c = compute_taxes_and_net(platform, gross)
        return jsonify(
            {
                "platform_fee": c.platform_fee,
                "withholding_1pct": c.withholding_1pct,
                "bir_8pct": c.bir_8pct,
                "net_profit": c.net_profit,
            }
        )

    @app.post("/api/sales/bulk")
    def api_sales_bulk():
        payload = request.get_json(silent=True)
        if isinstance(payload, list):
            rows = payload
        else:
            payload = payload or {}
            rows = payload.get("rows") or []
        if not isinstance(rows, list):
            return jsonify({"ok": False, "error": "rows must be a list"}), 400

        normalized: list[dict[str, Any]] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            try:
                d = parse_iso_date(r.get("date") or date.today().isoformat())
            except Exception:
                return jsonify({"ok": False, "error": "Invalid date format (use YYYY-MM-DD)"}), 400

            platform = (r.get("platform") or "").strip()
            order_id = (r.get("order_id") or "").strip()
            gross = float(r.get("gross_amount") or 0.0)
            c = compute_taxes_and_net(platform, gross)

            normalized.append(
                {
                    "type": "sale",
                    "date": d.isoformat(),
                    "platform": platform,
                    "order_id": order_id,
                    "gross_amount": round(gross, 2),
                    "platform_fee": c.platform_fee,
                    "withholding_1pct": c.withholding_1pct,
                    "bir_8pct": c.bir_8pct,
                    "net_profit": c.net_profit,
                }
            )

        # Save locally (demo store)
        app.config["TXNS"].extend(normalized)

        # Forward to Google Apps Script (optional)
        script_url = app.config["GOOGLE_SCRIPT_URL"]
        gas_result: dict[str, Any] | None = None
        if script_url:
            try:
                resp = requests.post(script_url, json=normalized, timeout=30)
                content_type = resp.headers.get("content-type", "")
                parsed: Any | None = None
                if "application/json" in content_type:
                    try:
                        parsed = resp.json()
                    except Exception:
                        parsed = None
                gas_result = {
                    "status_code": resp.status_code,
                    "ok": bool(resp.ok),
                    "json": parsed,
                    "text": resp.text[:2000],
                }
            except Exception as e:
                gas_result = {"error": str(e)}

        if gas_result and gas_result.get("error"):
            return jsonify({"ok": False, "error": gas_result["error"], "gas": gas_result}), 502
        if gas_result and gas_result.get("status_code") and not gas_result.get("ok", True):
            return jsonify({"ok": False, "error": "Google Script returned an error", "gas": gas_result}), 502

        return jsonify({"ok": True, "count": len(normalized), "gas": gas_result})

    @app.post("/api/expenses/bulk")
    def api_expenses_bulk():
        payload = request.get_json(silent=True)
        if isinstance(payload, list):
            rows = payload
        else:
            payload = payload or {}
            rows = payload.get("rows") or []
        if not isinstance(rows, list):
            return jsonify({"ok": False, "error": "rows must be a list"}), 400

        normalized: list[dict[str, Any]] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            try:
                d = parse_iso_date(r.get("date") or date.today().isoformat())
            except Exception:
                return jsonify({"ok": False, "error": "Invalid date format (use YYYY-MM-DD)"}), 400

            category = (r.get("category") or "").strip()
            desc = (r.get("description") or "").strip()
            amount = float(r.get("amount") or 0.0)

            normalized.append(
                {
                    "type": "expense",
                    "date": d.isoformat(),
                    "category": category,
                    "description": desc,
                    "amount": round(amount, 2),
                }
            )

        app.config["EXPENSES"].extend(normalized)

        script_url = app.config["GOOGLE_SCRIPT_URL"]
        gas_result: dict[str, Any] | None = None
        if script_url:
            try:
                resp = requests.post(script_url, json=normalized, timeout=30)
                content_type = resp.headers.get("content-type", "")
                parsed: Any | None = None
                if "application/json" in content_type:
                    try:
                        parsed = resp.json()
                    except Exception:
                        parsed = None
                gas_result = {
                    "status_code": resp.status_code,
                    "ok": bool(resp.ok),
                    "json": parsed,
                    "text": resp.text[:2000],
                }
            except Exception as e:
                gas_result = {"error": str(e)}

        if gas_result and gas_result.get("error"):
            return jsonify({"ok": False, "error": gas_result["error"], "gas": gas_result}), 502
        if gas_result and gas_result.get("status_code") and not gas_result.get("ok", True):
            return jsonify({"ok": False, "error": "Google Script returned an error", "gas": gas_result}), 502

        return jsonify({"ok": True, "count": len(normalized), "gas": gas_result})

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/go")
    def go():
        return redirect(url_for("dashboard"))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

