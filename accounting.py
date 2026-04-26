from __future__ import annotations

from dataclasses import dataclass
from datetime import date


PLATFORMS = ("Shopee", "Lazada", "TikTok")


@dataclass(frozen=True)
class ComputedAmounts:
    platform_fee: float
    withholding_1pct: float
    bir_8pct: float
    net_profit: float


def _round2(x: float) -> float:
    return float(f"{x:.2f}")


def estimate_platform_fee(platform: str, gross_amount: float) -> float:
    """
    Heuristic fee estimator (seller-friendly, conservative).
    You can later replace these with actual fee schedules per category/promo.
    """
    p = (platform or "").strip()
    g = max(0.0, float(gross_amount or 0.0))

    # Common blended estimates (commission + transaction + service), configurable later.
    rates = {
        "Shopee": 0.060,  # ~6%
        "Lazada": 0.055,  # ~5.5%
        "TikTok": 0.050,  # ~5%
    }
    rate = rates.get(p, 0.0)
    return _round2(g * rate)


def compute_taxes_and_net(platform: str, gross_amount: float) -> ComputedAmounts:
    g = max(0.0, float(gross_amount or 0.0))
    fee = estimate_platform_fee(platform, g)

    # PH E-commerce withholding tax (simplified 1% of gross receipts).
    wht = _round2(g * 0.01)

    # PH 8% flat rate (simplified: 8% of gross less platform fees).
    # Note: This is an estimate; official computation depends on registration/thresholds.
    bir8_base = max(0.0, g - fee)
    bir8 = _round2(bir8_base * 0.08)

    net = _round2(g - fee - wht - bir8)
    return ComputedAmounts(platform_fee=fee, withholding_1pct=wht, bir_8pct=bir8, net_profit=net)


def parse_iso_date(s: str) -> date:
    return date.fromisoformat((s or "").strip())

