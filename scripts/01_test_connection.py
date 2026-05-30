#!/usr/bin/env python3
"""Step 1: verify Tally HTTP server is reachable."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tally_client import TALLY_URL, check_connection


def main() -> int:
    print(f"Checking {TALLY_URL} ...")
    ok, msg = check_connection()
    if ok:
        print("OK:", msg)
        return 0
    print("FAILED:", msg)
    print()
    print("Fix checklist:")
    print("  1. Tally Prime is open (not just installed)")
    print("  2. A company is loaded (Gateway -> select company)")
    print("  3. F1 Help -> Settings -> Advanced -> HTTP Server = Yes, port 9000")
    print("  4. F11 Features -> Advanced -> Allow XML/HTTP Remote API = Yes")
  return 1


if __name__ == "__main__":
    raise SystemExit(main())
