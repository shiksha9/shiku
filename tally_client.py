"""Minimal client for Tally Prime XML/HTTP API (port 9000)."""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

TALLY_HOST = os.getenv("TALLY_HOST", "localhost")
TALLY_PORT = int(os.getenv("TALLY_PORT", "9000"))
TALLY_COMPANY = os.getenv("TALLY_COMPANY", "").strip()
TALLY_URL = f"http://{TALLY_HOST}:{TALLY_PORT}"

# Tally sometimes embeds control chars that break ElementTree.
_INVALID_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_xml(text: str) -> str:
    return _INVALID_XML_CHARS.sub("", text)


def parse_xml(text: str) -> ET.Element:
    return ET.fromstring(sanitize_xml(text))


def _company_block() -> str:
    if not TALLY_COMPANY:
        return ""
    return f"<SVCURRENTCOMPANY>{TALLY_COMPANY}</SVCURRENTCOMPANY>"


def post_xml(xml_body: str, timeout: int = 60) -> str:
    response = requests.post(
        TALLY_URL,
        data=xml_body.encode("utf-8"),
        headers={"Content-Type": "text/xml"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def check_connection() -> tuple[bool, str]:
    """Returns (ok, message). Tally returns plain text when idle."""
    try:
        raw = post_xml("", timeout=5)
        if "TallyPrime Server is Running" in raw or "Tally.ERP" in raw:
            return True, raw.strip()
        return True, f"Connected (response: {raw[:200]!r})"
    except requests.exceptions.ConnectionError:
        return (
            False,
            f"Cannot reach Tally at {TALLY_URL}. Is Tally open with HTTP/XML enabled?",
        )
    except requests.RequestException as exc:
        return False, str(exc)


def export_report(report_name: str, extra_static: str = "") -> str:
    xml = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>{report_name}</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        {_company_block()}
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        {extra_static}
      </STATICVARIABLES>
    </DESC>
  </BODY>
</ENVELOPE>"""
    return post_xml(xml)


def export_sundry_debtors_collection() -> str:
    """Export only ledger accounts under the Sundry Debtors group."""
    xml = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Sundry Debtor Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        {_company_block()}
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Sundry Debtor Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <CHILDOF>Sundry Debtors</CHILDOF>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
    return post_xml(xml)


def export_collection(collection_id: str) -> str:
    xml = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>{collection_id}</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        {_company_block()}
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
    </DESC>
  </BODY>
</ENVELOPE>"""
    return post_xml(xml)


def response_ok(xml_text: str) -> bool:
    try:
        root = parse_xml(xml_text)
    except ET.ParseError:
        return "STATUS" not in xml_text or "<STATUS>1</STATUS>" in xml_text
    status = root.find(".//STATUS")
    if status is not None and status.text == "0":
        return False
    line_error = root.find(".//LINEERROR")
    if line_error is not None and (line_error.text or "").strip():
        return False
    return True


def print_response_hint(xml_text: str) -> None:
    try:
        root = parse_xml(xml_text)
    except ET.ParseError:
        print(xml_text[:2000])
        return
    err = root.find(".//LINEERROR")
    if err is not None and err.text:
        print("Tally error:", err.text.strip())
    status = root.find(".//STATUS")
    if status is not None:
        print("STATUS:", status.text)
