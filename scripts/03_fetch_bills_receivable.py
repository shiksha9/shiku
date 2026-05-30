#!/usr/bin/env python3
"""Step 3: outstanding receivables (credit given bill-by-bill).

Requires: party ledgers have 'Maintain balances bill-by-bill' enabled in Tally.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tally_client import export_report, print_response_hint, response_ok

OUT = Path(__file__).resolve().parents[1] / "output" / "bills_receivable.xml"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("Fetching Bills Receivable ...")
    xml = export_report("Bills Receivable")
    OUT.write_text(xml, encoding="utf-8")
    print(f"Saved: {OUT} ({len(xml)} bytes)")
    if not response_ok(xml):
        print_response_hint(xml)
        print()
        print("If empty or error: in Tally open Display -> Outstandings -> Receivables")
        print("and confirm the report works there first.")
        return 1
    print("Done. Look for BILLDATE, BILLPARTY, BILLFINAL / pending amounts in the XML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
