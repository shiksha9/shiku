#!/usr/bin/env python3
"""Step 2: export all ledgers (names + closing balances)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tally_client import export_collection, print_response_hint, response_ok

OUT = Path(__file__).resolve().parents[1] / "output" / "ledgers.xml"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("Fetching List of Ledgers ...")
    xml = export_collection("List of Ledgers")
    OUT.write_text(xml, encoding="utf-8")
    print(f"Saved: {OUT} ({len(xml)} bytes)")
    if not response_ok(xml):
        print_response_hint(xml)
        return 1
    print("Done. Open output/ledgers.xml — search for Sundry Debtors / party names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
