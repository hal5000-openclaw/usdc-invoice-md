# usdc-invoice-md

A lightweight Python CLI that converts a CSV of line items into a Markdown invoice with exact Decimal totals and a USDC-on-Base payment footer.

## What
Read `description,quantity,unit_price` rows, compute subtotal/tax/total with `decimal.Decimal`, and output Markdown.

## Why
Generate reproducible invoices with precise math, no floating point drift, and clear payment instructions for USDC on Base.

## Install
No dependencies required (Python standard library only).

```bash
git clone <repo>
cd usdc-invoice-md
```

Optional: create a venv and install pytest for tests.
```bash
python3 -m venv venv
source venv/bin/activate
pip install pytest
```

## Usage

Basic:
```bash
python invoice.py items.csv --client "Acme Corp" --wallet 0x1234567890abcdef1234567890abcdef12345678
```

With tax:
```bash
python invoice.py items.csv --client "Acme Corp" --wallet 0x1234567890abcdef1234567890abcdef12345678 --tax 10
```

Optional date and output:
```bash
python invoice.py items.csv --client "Acme Corp" --wallet 0x1234567890abcdef1234567890abcdef12345678 --date 2026-10-16
```

CSV columns (case-insensitive): `description`, `quantity`, `unit_price`.

Example output:
```markdown
# Invoice for Acme Corp
Date: 2026-10-16

| Description | Quantity | Unit Price | Amount |
|-------------|----------|------------|--------|
| Consulting | 1 | $100.00 | $100.00 |
...

Subtotal: $326.75
Tax: $0.00
Total: $326.75

## Payment Instructions
Pay with USDC on Base network to the following address:
Wallet: 0x1234567890abcdef1234567890abcdef12345678
Network: Base
```

## Tests
```bash
pytest -q
```
