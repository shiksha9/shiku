#!/usr/bin/env python3
"""
Fetch Sundry Debtors (customer) ledgers from Tally.

Why your earlier script failed:
1. Wrong XML shape — Tally answered with Import/All Masters (currencies), not ledgers.
2. ParseError — Tally XML often has illegal control characters; we strip them first.

Run: python scripts/04_sundry_debtors.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tally_client import (
    TALLY_COMPANY,
    export_collection,
    export_sundry_debtors_collection,
    parse_xml,
    print_response_hint,
    response_ok,
    sanitize_xml,
)

OUT = Path(__file__).resolve().parents[1] / "output" / "sundry_debtors.xml"
DEBTOR_PARENT_HINT = "sundry debtor"


def _text(el) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def parse_debtors_from_ledgers(xml_text: str) -> list[dict]:
    root = parse_xml(xml_text)
    debtors: list[dict] = []

    for ledger in root.iter("LEDGER"):
        name = _text(ledger.find("NAME"))
        if not name:
            # Collection export often uses NAME.LIST / NAME
            for name_el in ledger.findall(".//NAME"):
                if _text(name_el):
                    name = _text(name_el)
                    break
        parent = _text(ledger.find("PARENT"))
        closing = _text(ledger.find("CLOSINGBALANCE")) or _text(
            ledger.find("CLOSINGBALANCES")
        )

        if DEBTOR_PARENT_HINT in parent.lower() or not parent:
            # When using filtered collection, PARENT may be a sub-group under Debtors
            if parent or name:
                debtors.append(
                    {"name": name, "parent": parent, "closing_balance": closing}
                )

    # De-dupe by name
    seen: set[str] = set()
    unique: list[dict] = []
    for row in debtors:
        key = row["name"].lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(row)
    return sorted(unique, key=lambda r: r["name"].lower())


def filter_true_sundry_debtors(rows: list[dict]) -> list[dict]:
    return [r for r in rows if DEBTOR_PARENT_HINT in r["parent"].lower()]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    company = TALLY_COMPANY or "(active company in Tally)"
    print(f"Company: {company}\n")

    print("Trying filtered export (ledgers under Sundry Debtors)...")
    xml = export_sundry_debtors_collection()
    OUT.write_text(sanitize_xml(xml), encoding="utf-8")

    if not response_ok(xml):
        print_response_hint(xml)
        print("\nFallback: full List of Ledgers, then filter by PARENT...")
        xml = export_collection("List of Ledgers")
        OUT.write_text(sanitize_xml(xml), encoding="utf-8")
        if not response_ok(xml):
            print_response_hint(xml)
            return 1
        rows = filter_true_sundry_debtors(parse_debtors_from_ledgers(xml))
    else:
        rows = parse_debtors_from_ledgers(xml)
        if not rows:
            print("Filtered export empty — trying full ledger list...")
            xml = export_collection("List of Ledgers")
            OUT.write_text(sanitize_xml(xml), encoding="utf-8")
            rows = filter_true_sundry_debtors(parse_debtors_from_ledgers(xml))

    print(f"\nSaved raw XML: {OUT}\n")
    print("SUNDRY DEBTORS")
    print("-" * 50)
    if not rows:
        print("No debtors found.")
        print("- Open output/sundry_debtors.xml and search for <LEDGER>")
        print("- In Tally: do you see parties under Accounts > Sundry Debtors?")
        return 1

    for i, row in enumerate(rows, 1):
        bal = row["closing_balance"] or "—"
        parent = f" ({row['parent']})" if row["parent"] else ""
        print(f"{i:3}. {row['name']}{parent}  balance: {bal}")

    print(f"\nTotal: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
