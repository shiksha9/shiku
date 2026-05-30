"""
Drop-in replacement for parse_debtors.py — copy to C:\\Projects\\tally-reminder\\
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

TALLY_URL = "http://localhost:9000"
# Set exact company name if you have multiple companies open in Tally
TALLY_COMPANY = "GANESH MARKETING"

_INVALID_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_xml(text: str) -> str:
    return _INVALID_XML_CHARS.sub("", text)


def fetch_sundry_debtors() -> str | None:
    company_tag = (
        f"<SVCURRENTCOMPANY>{TALLY_COMPANY}</SVCURRENTCOMPANY>" if TALLY_COMPANY else ""
    )

    # CORRECT request: Export + Collection (not "Export Data" + wrong report layout)
    xml_request = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>List of Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        {company_tag}
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
    </DESC>
  </BODY>
</ENVELOPE>"""

    try:
        res = requests.post(
            TALLY_URL,
            data=xml_request.encode("utf-8"),
            headers={"Content-Type": "text/xml"},
            timeout=120,
        )
        res.raise_for_status()
        print("Connected to Tally")
        return sanitize_xml(res.text)
    except Exception as e:
        print("Error:", e)
        return None


def parse_debtors(xml_data: str) -> list[str]:
    root = ET.fromstring(xml_data)
    names: list[str] = []

    for ledger in root.iter("LEDGER"):
        parent_el = ledger.find("PARENT")
        parent = (parent_el.text or "").strip() if parent_el is not None else ""

        if "sundry debtor" not in parent.lower():
            continue

        name_el = ledger.find("NAME")
        name = (name_el.text or "").strip() if name_el is not None else ""
        if not name:
            for n in ledger.findall(".//NAME"):
                if n.text and n.text.strip():
                    name = n.text.strip()
                    break
        if name:
            names.append(name)

    return sorted(set(names), key=str.lower)


def main() -> None:
    xml = fetch_sundry_debtors()
    if not xml:
        sys.exit(1)

    if "Import Data" in xml[:500] and "List of Ledgers" not in xml[:800]:
        print("Warning: response looks like wrong export (Import/All Masters).")
        print("First 400 chars:", xml[:400])

    try:
        debtors = parse_debtors(xml)
    except ET.ParseError as e:
        print("XML parse failed even after sanitize:", e)
        print("Save full response to debug.xml and open in a text editor.")
        Path = __import__("pathlib").Path
        Path("debug.xml").write_text(xml, encoding="utf-8")
        sys.exit(1)

    print("\nSUNDRY DEBTORS")
    print("-" * 40)
    if not debtors:
        print("No debtors found. Check PARENT names in debug.xml (sub-groups?).")
        sys.exit(1)
    for i, name in enumerate(debtors, 1):
        print(f"{i}. {name}")


if __name__ == "__main__":
    main()
