"""
Email utilities for TV Ratings Automation.

Two responsibilities:
  1. fetch_ratings_credentials() — connect to Gmail, find today's email, extract password + link
  2. send_report() — send an HTML report via SMTP
"""

import imaplib
import email
import os
import re
import smtplib
import datetime

from email.header import decode_header
from email.message import Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


# ── Extraction helpers (private) ─────────────────────────────────────

def _decode_payload(part: Message) -> str | None:
    payload = part.get_payload(decode=True)
    if not payload:
        return None
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _extract_text_body(msg: Message) -> str:
    def extract_parts(target_type: str) -> list[str]:
        chunks = []
        parts = msg.walk() if msg.is_multipart() else [msg]
        for part in parts:
            content_type = (part.get_content_type() or "").lower()
            disposition = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disposition:
                continue
            if content_type == target_type:
                decoded = _decode_payload(part)
                if decoded:
                    chunks.append(decoded)
        return chunks

    text_chunks = extract_parts("text/plain")
    body = "\n".join(c.strip() for c in text_chunks if c and c.strip())

    if not body:
        html = "\n".join(extract_parts("text/html"))
        if html:
            body = re.sub(r"<[^>]+>", " ", html)
            body = re.sub(r"\s+", " ", body).strip()

    return body


def _extract_password(body: str) -> str | None:
    if not body:
        return None
    match = re.search(r"(?im)^\s*password\s*:\s*([0-9]+)\s*$", body)
    if match:
        return match.group(1)
    match = re.search(r"(?i)\bpassword\s*:\s*([0-9]+)\b", body)
    return match.group(1) if match else None


def _extract_link(body: str) -> str | None:
    if not body:
        return None
    match = re.search(r"https://[^\s<>()\"']+", body, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(0).rstrip(".,;:!?)\"]'")


# ── Public API ────────────────────────────────────────────────────────

def fetch_ratings_credentials(use_yesterday: bool = False) -> tuple[str, str] | None:
    """Connect to Gmail, search for today's ratings email, extract (password, link).

    Args:
        use_yesterday: Search yesterday's date instead of today's.

    Returns:
        (password, link) if found, None if email hasn't arrived yet.

    Raises:
        ConnectionError: If Gmail connection fails.
    """
    offset = 1 if use_yesterday else 0
    search_date = (datetime.datetime.today() - timedelta(days=offset)).strftime("%d-%b-%Y")

    logger.info(f"Searching for ratings email from {search_date}")

    conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    try:
        conn.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        conn.select("INBOX")

        status, message_ids = conn.search(None, "ON", search_date)
        if status != "OK":
            logger.error("IMAP search failed")
            return None

        email_ids = message_ids[0].split()
        if not email_ids:
            logger.info("No emails found — ratings email hasn't arrived yet")
            return None

        logger.info(f"Found {len(email_ids)} email(s), scanning for credentials...")

        for eid in email_ids:
            status, msg_data = conn.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            body = _extract_text_body(msg)

            password = _extract_password(body)
            link = _extract_link(body)

            if password and link:
                logger.info(f"Credentials found — password: {password}, link: {link}")
                return password, link

        logger.info("No valid credentials found in any email")
        return None

    finally:
        try:
            conn.logout()
        except Exception:
            pass


def send_report(report_html: str, recipient: str) -> None:
    """Send an HTML report email.

    Args:
        report_html: HTML content of the report.
        recipient: Destination email address.
    """
    yesterday = datetime.datetime.today() - timedelta(days=1)
    subject = f"Audiente {yesterday.strftime('%d.%m.%Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg.attach(MIMEText(report_html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
        logger.info(f"Report sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send report to {recipient}: {e}")