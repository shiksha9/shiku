# Shiku — Tally credit reminders (Phase 1: get data)

Phase 1 pulls data from **Tally on your PC** via its built-in XML/HTTP API (port **9000**). The daily reminder logic comes later; first make sure these three scripts work.

## Part A — Turn on Tally’s API (one time)

Do this **on the same computer where Tally runs**:

1. **Open Tally Prime** and **load your father’s company** (not just the gateway screen).
2. **Enable HTTP server**
   - Press **F1** (Help) → **Settings** → **Advanced Configuration** (or **Connectivity** in some versions).
   - Set **HTTP Server** = **Yes**
   - Port = **9000** (default).
3. **Enable XML API** (wording varies by version)
   - **F11** (Features) → **Advanced Configuration** / **Advanced Features**
   - **Allow XML over HTTP** / **Allow XML/HTTP Remote API** = **Yes**
4. If Windows Firewall asks, **allow Tally** on private networks.

**Quick test without Python** — in Command Prompt or PowerShell:

```bat
curl http://localhost:9000
```

You should see something like: `TallyPrime Server is Running on port 9000`

If `curl` fails: Tally is closed, company not loaded, HTTP not enabled, or wrong port.

## Part B — Run the scripts on your PC

Tally cannot be reached from this cloud repo; clone/download this project **on your Windows machine** (same PC as Tally).

```bat
cd path\to\shiku
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` if needed:

- `TALLY_HOST=localhost`
- `TALLY_PORT=9000`
- `TALLY_COMPANY=` exact name from Tally’s title bar (optional but helps if multiple companies exist)

Run in order:

```bat
python scripts\01_test_connection.py
python scripts\02_fetch_ledgers.py
python scripts\03_fetch_bills_receivable.py
```

Outputs:

- `output\ledgers.xml` — all ledgers and balances
- `output\bills_receivable.xml` — **who owes money, bill date, pending amount** (best for 15-day reminders)

## Part C — Tally settings your father likely needs

For credit / “udhaar” tracking, each **customer ledger** should have:

- **Maintain balances bill-by-bill** = Yes  
  (Alter Ledger → set in billing settings)
- Sales on credit entered as **Credit** with bill reference (not only cash)

Then **Display → Statements of Accounts → Outstandings → Receivables** should show rows. If that screen is empty in Tally, the XML export will be empty too.

## Fix for “Import Data / All Masters” + XML ParseError

If your script prints currencies (`CURRENCY`, `All Masters`) instead of ledgers, the XML request shape is wrong. Use **Export + Collection + List of Ledgers**, not `Export Data` + `List of Accounts`.

If you get `ParseError: reference to invalid character number`, Tally returned illegal control characters. Strip them before parsing:

```python
import re
INVALID = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
xml = INVALID.sub("", response.text)
```

Copy `parse_debtors_fixed.py` into your project, or run:

```bat
python scripts\04_sundry_debtors.py
```

Set `TALLY_COMPANY=GANESH MARKETING` in `.env` (exact spelling as in Tally).

## Common problems

| Symptom | What to do |
|--------|------------|
| Connection refused | Tally not open, or HTTP Server off, or wrong port |
| Empty bills XML | Bill-by-bill not enabled on debtor ledgers; or no credit sales |
| Wrong company data | Set `TALLY_COMPANY` in `.env` to exact company name |
| `LINEERROR` in XML | Company not loaded; or report name mismatch — try opening Receivables in Tally first |

## Phase 2 (later)

- Parse `bills_receivable.xml`, compute days since bill date
- If ≥ 15 days, add to “call today” list
- Schedule `01` → `03` daily (Windows Task Scheduler)
