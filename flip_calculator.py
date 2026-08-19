"""
flip_calculator.py

CLI tool to calculate profit/ROI for flipping/reselling items.
Supports single-item calculation via command-line arguments and batch processing via CSV input/output.

Inputs (CSV headers or CLI args):
  purchase_price, selling_price, quantity (default 1), shipping_in_cost, shipping_out_cost,
  platform_fee_percent, fixed_platform_fees, refurbishment_cost, listing_fee, taxes_percent,
  storage_cost_per_day, days_to_sell, other_fees

Outputs (printed and/or CSV):
  gross_profit, net_profit, ROI_percent, ROI_per_day, break_even_selling_price,
  required_selling_price_for_target_ROI, total_costs

Usage examples:
  python flip_calculator.py --purchase-price 10 --selling-price 30 --platform-fee-percent 10
  python flip_calculator.py --csv input.csv --output results.csv
"""
from __future__ import annotations
import argparse
import csv
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List


@dataclass
class FlipItem:
    purchase_price: float
    selling_price: Optional[float] = None
    quantity: int = 1
    shipping_in_cost: float = 0.0
    shipping_out_cost: float = 0.0
    platform_fee_percent: float = 0.0  # percent, e.g., 10 for 10%
    fixed_platform_fees: float = 0.0
    refurbishment_cost: float = 0.0
    listing_fee: float = 0.0
    taxes_percent: float = 0.0  # percent applied to profit
    storage_cost_per_day: float = 0.0
    days_to_sell: float = 0.0
    other_fees: float = 0.0


def parse_float(x: str, default: float = 0.0) -> float:
    if x is None or x == "":
        return default
    try:
        return float(x)
    except ValueError:
        return default


def compute_totals(item: FlipItem) -> Dict[str, Any]:
    q = max(1, int(item.quantity))
    p_pct = item.platform_fee_percent / 100.0
    t_pct = item.taxes_percent / 100.0

    fixed_costs = (
        item.purchase_price * q
        + item.refurbishment_cost * q
        + item.shipping_in_cost * q
        + item.shipping_out_cost * q
        + item.listing_fee
        + item.fixed_platform_fees
        + item.storage_cost_per_day * item.days_to_sell * q
        + item.other_fees
    )

    selling_price = item.selling_price if item.selling_price is not None else 0.0

    gross_revenue = selling_price * q
    platform_fee_amount = p_pct * gross_revenue

    gross_profit = gross_revenue - fixed_costs - platform_fee_amount
    # taxes apply to profit (if profit > 0)
    taxes = 0.0
    if gross_profit > 0:
        taxes = gross_profit * t_pct

    net_profit = gross_profit - taxes

    roi_percent = (net_profit / fixed_costs * 100.0) if fixed_costs != 0 else None
    roi_per_day = (roi_percent / item.days_to_sell) if (roi_percent is not None and item.days_to_sell > 0) else None

    # break-even selling price per item (solve for S):
    # (S*q*(1 - p_pct)) - fixed_costs = 0 -> S = fixed_costs / (q*(1 - p_pct))
    denom = q * (1.0 - p_pct)
    break_even_selling_price = (fixed_costs / denom) if denom > 0 else None

    return {
        "quantity": q,
        "fixed_costs": round(fixed_costs, 2),
        "gross_revenue": round(gross_revenue, 2),
        "platform_fee_amount": round(platform_fee_amount, 2),
        "gross_profit": round(gross_profit, 2),
        "taxes": round(taxes, 2),
        "net_profit": round(net_profit, 2),
        "ROI_percent": round(roi_percent, 2) if roi_percent is not None else None,
        "ROI_per_day": round(roi_per_day, 4) if roi_per_day is not None else None,
        "break_even_selling_price": round(break_even_selling_price, 2) if break_even_selling_price is not None else None,
    }


def required_selling_price_for_target(item: FlipItem, target_roi_percent: float) -> Optional[float]:
    # Solve for S in: ((S*q*(1 - p) - F) * (1 - t)) / F = target_roi
    q = max(1, int(item.quantity))
    p = item.platform_fee_percent / 100.0
    t = item.taxes_percent / 100.0

    F = (
        item.purchase_price * q
        + item.refurbishment_cost * q
        + item.shipping_in_cost * q
        + item.shipping_out_cost * q
        + item.listing_fee
        + item.fixed_platform_fees
        + item.storage_cost_per_day * item.days_to_sell * q
        + item.other_fees
    )

    if F <= 0 or (1 - p) <= 0 or (1 - t) <= 0:
        return None

    target_ratio = target_roi_percent / 100.0
    # S = ( F + (target_ratio * F) / (1 - t) ) / ( q*(1 - p) )
    numerator = F + (target_ratio * F) / (1.0 - t)
    denom = q * (1.0 - p)
    return round(numerator / denom, 2)


def validate_item(item: FlipItem) -> None:
    """Validate input fields of a FlipItem. Raises ValueError for invalid values."""
    if item.purchase_price < 0:
        raise ValueError("purchase_price must be >= 0")
    if item.quantity < 1:
        raise ValueError("quantity must be >= 1")
    for name in ("shipping_in_cost", "shipping_out_cost", "fixed_platform_fees", "refurbishment_cost", "listing_fee", "storage_cost_per_day", "other_fees"):
        if getattr(item, name) < 0:
            raise ValueError(f"{name} must be >= 0")
    if not (0.0 <= item.platform_fee_percent <= 100.0):
        raise ValueError("platform_fee_percent must be between 0 and 100")
    if not (0.0 <= item.taxes_percent <= 100.0):
        raise ValueError("taxes_percent must be between 0 and 100")
    if item.days_to_sell < 0:
        raise ValueError("days_to_sell must be >= 0")


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def write_csv(path: str, rows: List[Dict[str, Any]]):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def make_item_from_row(row: Dict[str, str]) -> FlipItem:
    return FlipItem(
        purchase_price=parse_float(row.get("purchase_price", "0")),
        selling_price=(parse_float(row.get("selling_price", "")) if row.get("selling_price", "") != "" else None),
        quantity=int(parse_float(row.get("quantity", "1"))),
        shipping_in_cost=parse_float(row.get("shipping_in_cost", "0")),
        shipping_out_cost=parse_float(row.get("shipping_out_cost", "0")),
        platform_fee_percent=parse_float(row.get("platform_fee_percent", "0")),
        fixed_platform_fees=parse_float(row.get("fixed_platform_fees", "0")),
        refurbishment_cost=parse_float(row.get("refurbishment_cost", "0")),
        listing_fee=parse_float(row.get("listing_fee", "0")),
        taxes_percent=parse_float(row.get("taxes_percent", "0")),
        storage_cost_per_day=parse_float(row.get("storage_cost_per_day", "0")),
        days_to_sell=parse_float(row.get("days_to_sell", "0")),
        other_fees=parse_float(row.get("other_fees", "0")),
    )


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_net = sum(r.get("net_profit", 0.0) for r in results)
    total_fixed = sum(r.get("fixed_costs", 0.0) for r in results)
    avg_roi = None
    try:
        avg_roi = round(sum(r.get("ROI_percent", 0.0) for r in results if r.get("ROI_percent") is not None) / len(results), 2)
    except Exception:
        avg_roi = None
    return {"total_net_profit": round(total_net, 2), "total_invested": round(total_fixed, 2), "average_ROI_percent": avg_roi}


def main():
    parser = argparse.ArgumentParser(description="Flip calculator for reselling items")
    parser.add_argument("--csv", help="Input CSV file for batch processing")
    parser.add_argument("--output", help="Output CSV file for batch results")
    parser.add_argument("--target-roi", type=float, help="Target ROI percent to compute required selling price")

    # Single item args
    parser.add_argument("--purchase-price", type=float, help="Purchase price")
    parser.add_argument("--selling-price", type=float, help="Selling price (optional for break-even/target calculations)")
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--shipping-in-cost", type=float, default=0.0)
    parser.add_argument("--shipping-out-cost", type=float, default=0.0)
    parser.add_argument("--platform-fee-percent", type=float, default=0.0)
    parser.add_argument("--fixed-platform-fees", type=float, default=0.0)
    parser.add_argument("--refurbishment-cost", type=float, default=0.0)
    parser.add_argument("--listing-fee", type=float, default=0.0)
    parser.add_argument("--taxes-percent", type=float, default=0.0)
    parser.add_argument("--storage-cost-per-day", type=float, default=0.0)
    parser.add_argument("--days-to-sell", type=float, default=0.0)
    parser.add_argument("--other-fees", type=float, default=0.0)

    args = parser.parse_args()

    results = []

    if args.csv:
        rows = read_csv(args.csv)
        for row in rows:
            item = make_item_from_row(row)
            totals = compute_totals(item)
            entry = {**{k: v for k, v in row.items()}, **totals}
            if args.target_roi is not None:
                entry["required_selling_price_for_target_ROI"] = required_selling_price_for_target(item, args.target_roi)
            results.append(entry)
        if args.output:
            write_csv(args.output, results)
        summary = summarize_results(results)
        print("Batch summary:", summary)
    else:
        if args.purchase_price is None:
            parser.error("--purchase-price is required for single-item mode")
        item = FlipItem(
            purchase_price=args.purchase_price,
            selling_price=args.selling_price,
            quantity=args.quantity,
            shipping_in_cost=args.shipping_in_cost,
            shipping_out_cost=args.shipping_out_cost,
            platform_fee_percent=args.platform_fee_percent,
            fixed_platform_fees=args.fixed_platform_fees,
            refurbishment_cost=args.refurbishment_cost,
            listing_fee=args.listing_fee,
            taxes_percent=args.taxes_percent,
            storage_cost_per_day=args.storage_cost_per_day,
            days_to_sell=args.days_to_sell,
            other_fees=args.other_fees,
        )
        totals = compute_totals(item)
        if args.target_roi is not None:
            totals["required_selling_price_for_target_ROI"] = required_selling_price_for_target(item, args.target_roi)
        print("Results:")
        for k, v in totals.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
