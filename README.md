Flip Calculator
===============

[![CI](https://github.com/primepike52/flip-calculator/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/primepike52/flip-calculator/actions)

A simple Python CLI tool to evaluate reselling/flipping items (single item or batch CSV).

Usage
-----

Single item via CLI:
  python flip_calculator.py \
    --purchase-price 10 \
    --selling-price 30 \
    --platform-fee-percent 10 \
    --refurbishment-cost 2 \
    --shipping-in-cost 0 \
    --shipping-out-cost 3 \
    --listing-fee 0.5 \
    --taxes-percent 15 \
    --days-to-sell 10

Batch CSV:
  Input CSV should have headers like: purchase_price,selling_price,quantity,shipping_in_cost,shipping_out_cost,platform_fee_percent,fixed_platform_fees,refurbishment_cost,listing_fee,taxes_percent,storage_cost_per_day,days_to_sell,other_fees

  python flip_calculator.py --csv input.csv --output results.csv --target-roi 30

Outputs
-------
The tool prints a small summary and (for CSV mode) writes the per-row results to the output CSV.

Notes
-----
- Taxes are applied as a percent of profit (if profit > 0).
- Platform percentage fees are applied to selling price (e.g., 10 means 10%).
- Break-even and required selling price assume taxes and platform percent are applied as configured.

Extending
---------
- Add sensitivity analysis or Monte Carlo to see ranges of outcomes.
- Build a small web UI for interactive exploration.

Running tests
-------------
This project includes pytest-based unit tests under the tests/ directory.

Install test dependencies (optional but recommended):
  pip install -r requirements.txt

Run tests with:
  pytest -q

CSV schema
----------
Input CSV should include the following headers (examples shown in example_input.csv):
- purchase_price: numeric
- selling_price: numeric (may be blank to compute break-even/required price)
- quantity: integer (default 1)
- shipping_in_cost, shipping_out_cost: numeric
- platform_fee_percent: percent (0-100)
- fixed_platform_fees: numeric
- refurbishment_cost: numeric
- listing_fee: numeric
- taxes_percent: percent applied to profit (0-100)
- storage_cost_per_day: numeric
- days_to_sell: numeric
- other_fees: numeric

The output CSV (when using --output) will include per-row computed fields such as: fixed_costs,gross_revenue,platform_fee_amount,gross_profit,taxes,net_profit,ROI_percent,ROI_per_day,break_even_selling_price,required_selling_price_for_target_ROI
