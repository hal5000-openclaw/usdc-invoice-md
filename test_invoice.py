import os
import subprocess
import sys
import tempfile
from decimal import Decimal
import pytest
from invoice import calculate_totals, validate_wallet_address, generate_markdown_invoice


@pytest.fixture
def sample_csv():
    csv_content = """description,quantity,unit_price
Consulting,1,100.00
Development,2,75.50
Testing,3,25.25
"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        f.write(csv_content)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_wallet_validation_valid():
    valid_addresses = [
        "0x1234567890abcdef1234567890abcdef12345678",
        "0xABCDEF1234567890abcdef1234567890ABCDEF12",
        "0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
    ]
    for address in valid_addresses:
        # function should not raise or exit
        validate_wallet_address(address)
        res = subprocess.run(
            [sys.executable, "invoice.py", "items.csv", "--client", "Test", "--wallet", address],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0


def test_wallet_validation_invalid():
    invalid_addresses = [
        "1234567890abcdef1234567890abcdef12345678",
        "0x1234567890abcdef1234567890abcdef1234567",
        "0x1234567890abcdef1234567890abcdef123456789",
        "0xGHIJKL1234567890abcdef1234567890ABCDEF12",
    ]
    for address in invalid_addresses:
        with pytest.raises(SystemExit) as exc_info:
            validate_wallet_address(address)
        assert exc_info.value.code == 1
        res = subprocess.run(
            [sys.executable, "invoice.py", "items.csv", "--client", "Test", "--wallet", address],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 1


def test_decimal_precision(sample_csv):
    res = subprocess.run(
        [sys.executable, "invoice.py", sample_csv, "--client", "Test", "--wallet", "0x1234567890abcdef1234567890abcdef12345678"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Subtotal: $326.75" in res.stdout
    assert "Tax: $0.00" in res.stdout
    assert "Total: $326.75" in res.stdout


def test_subtotal_and_tax_calculation(sample_csv):
    res = subprocess.run(
        [sys.executable, "invoice.py", sample_csv, "--client", "Test", "--wallet", "0x1234567890abcdef1234567890abcdef12345678", "--tax", "10"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Subtotal: $326.75" in res.stdout
    assert "Tax: $32.68" in res.stdout
    assert "Total: $359.43" in res.stdout


def test_markdown_rendering(sample_csv):
    res = subprocess.run(
        [sys.executable, "invoice.py", sample_csv, "--client", "Acme", "--wallet", "0x1234567890abcdef1234567890abcdef12345678", "--date", "2026-10-16"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "# Invoice for Acme" in res.stdout
    assert "Date: 2026-10-16" in res.stdout
    assert "| Description | Quantity | Unit Price | Amount |" in res.stdout
    assert "| Consulting | 1 | $100.00 | $100.00 |" in res.stdout
    assert "## Payment Instructions" in res.stdout
    assert "Pay with USDC on Base network to the following address:" in res.stdout
    assert "Wallet: 0x1234567890abcdef1234567890abcdef12345678" in res.stdout
    assert "Network: Base" in res.stdout


def test_cli_execution():
    res = subprocess.run(
        [sys.executable, "invoice.py", "items.csv", "--client", "Alpha Corp", "--wallet", "0x1234567890abcdef1234567890abcdef12345678"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Invoice for Alpha Corp" in res.stdout
    assert "Consulting" in res.stdout


def test_output_to_file(sample_csv, tmp_path):
    out_file = str(tmp_path / "invoice.md")
    res = subprocess.run(
        [sys.executable, "invoice.py", sample_csv, "--client", "Beta", "--wallet", "0x1234567890abcdef1234567890abcdef12345678", "--output", out_file],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert os.path.exists(out_file)
    with open(out_file, encoding="utf-8") as f:
        content = f.read()
    assert "Invoice for Beta" in content
