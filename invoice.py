import argparse
import csv
import re
import sys
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def validate_wallet_address(address):
    """Validate a Base EVM wallet address."""
    if not re.match(r"^0x[0-9a-fA-F]{40}$", address):
        print(f"Error: Invalid wallet address: {address}", file=sys.stderr)
        sys.exit(1)


def calculate_totals(items, tax_pct=0):
    """Calculate subtotal, tax, and total with Decimal precision."""
    subtotal = sum(
        (Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])) for item in items),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    tax_rate = Decimal(str(tax_pct)) / Decimal("100")
    tax = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = subtotal + tax
    return subtotal, tax, total


def generate_markdown_invoice(client, wallet, items, subtotal, tax, total, date):
    """Generate Markdown invoice string."""
    lines = [
        f"# Invoice for {client}",
        f"Date: {date}",
        "",
        "| Description | Quantity | Unit Price | Amount |",
        "|-------------|----------|------------|--------|",
    ]
    for item in items:
        qty = Decimal(str(item["quantity"]))
        unit_price = Decimal(str(item["unit_price"]))
        amount = (qty * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lines.append(f"| {item['description']} | {item['quantity']} | ${unit_price:.2f} | ${amount:.2f} |")

    lines.extend([
        "",
        f"Subtotal: ${subtotal:.2f}",
        f"Tax: ${tax:.2f}",
        f"Total: ${total:.2f}",
        "",
        "## Payment Instructions",
        "Pay with USDC on Base network to the following address:",
        f"Wallet: {wallet}",
        "Network: Base",
    ])
    return "\n".join(lines)


def parse_csv_items(csv_path):
    """Parse line items from CSV file with column name normalization."""
    items = []
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return items
        mapping = {}
        for idx, col in enumerate(header):
            col_key = col.strip().lower()
            if col_key in ("description", "desc", "item"):
                mapping["description"] = idx
            elif col_key in ("quantity", "qty", "count"):
                mapping["quantity"] = idx
            elif col_key in ("unit_price", "price", "rate", "cost"):
                mapping["unit_price"] = idx

        for row in reader:
            if not row or all(c.strip() == "" for c in row):
                continue
            desc = row[mapping.get("description", 0)].strip()
            qty = row[mapping.get("quantity", 1)].strip()
            price = row[mapping.get("unit_price", 2)].strip()
            items.append({"description": desc, "quantity": qty, "unit_price": price})
    return items


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a USDC invoice from a CSV file.")
    parser.add_argument("csv_file", help="Path to the CSV file containing line items")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--wallet", required=True, help="Base wallet address")
    parser.add_argument("--tax", type=float, default=0.0, help="Tax percentage")
    parser.add_argument("--date", help="Invoice date (YYYY-MM-DD)")
    parser.add_argument("--output", help="Output file path (default stdout)")

    args = parser.parse_args(argv)

    validate_wallet_address(args.wallet)
    items = parse_csv_items(args.csv_file)
    subtotal, tax, total = calculate_totals(items, args.tax)
    date_str = args.date if args.date else datetime.now().strftime("%Y-%m-%d")

    invoice_md = generate_markdown_invoice(args.client, args.wallet, items, subtotal, tax, total, date_str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(invoice_md + "\n")
    else:
        print(invoice_md)


if __name__ == "__main__":
    main()
