import imaplib
import email
import os
import datetime
import re

from email.header import decode_header
from email.message import Message
from datetime import timedelta
from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# ============ CONFIG ============
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

DATE_TODAY = datetime.datetime.today().strftime("%d-%b-%Y")  # IMAP format, e.g. 28-Jan-2026
DATE_OF_DATA = (datetime.datetime.today() - timedelta(days=1)).strftime("%d.%m")  # Digi email format eg. 01.01.
                                                                                  # No year to account for wrong dates


class EmailService:
    """Service for connecting to Gmail and retrieving ratings emails."""

    def __init__(self):
        self.imap_server = IMAP_SERVER
        self.imap_port = IMAP_PORT
        self.email = EMAIL_ADDRESS
        self.password = EMAIL_PASSWORD
        self.connection = None

    def connect(self) -> bool:
        """Establish connection to Gmail IMAP server."""
        try:
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.connection.login(self.email, self.password)
            logger.info("✓ Connected to Gmail")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False
    def disconnect(self):
        """Close the IMAP connection."""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass

    def _extract_text_body(self, msg: Message) -> str:
        """Best-effort extraction of a readable text body from an email message."""
        text_chunks: list[str] = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = (part.get_content_type() or "").lower()
                content_disposition = (part.get("Content-Disposition") or "").lower()

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            text_chunks.append(payload.decode(charset, errors="replace"))
                        except LookupError:
                            text_chunks.append(payload.decode("utf-8", errors="replace"))
        else:
            if (msg.get_content_type() or "").lower() == "text/plain":
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    try:
                        text_chunks.append(payload.decode(charset, errors="replace"))
                    except LookupError:
                        text_chunks.append(payload.decode("utf-8", errors="replace"))

        body_text = "\n".join(chunk.strip() for chunk in text_chunks if chunk and chunk.strip())

        # If there's no text/plain part, fall back to a very rough HTML->text strip.
        if not body_text:
            html_chunks: list[str] = []
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = (part.get_content_type() or "").lower()
                    content_disposition = (part.get("Content-Disposition") or "").lower()
                    if "attachment" in content_disposition:
                        continue
                    if content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            try:
                                html_chunks.append(payload.decode(charset, errors="replace"))
                            except LookupError:
                                html_chunks.append(payload.decode("utf-8", errors="replace"))
            else:
                if (msg.get_content_type() or "").lower() == "text/html":
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or "utf-8"
                        try:
                            html_chunks.append(payload.decode(charset, errors="replace"))
                        except LookupError:
                            html_chunks.append(payload.decode("utf-8", errors="replace"))

            html = "\n".join(html_chunks)
            if html:
                # crude but dependency-free: remove tags
                body_text = re.sub(r"<[^>]+>", " ", html)
                body_text = re.sub(r"\s+", " ", body_text).strip()

        return body_text
    def get_email_details(self, email_id: bytes) -> dict:
        """Fetch basic details of an email.

        Args:
            email_id: Email ID from search results

        Returns:
            dict: Email details (subject, from, date, body)
        """
        try:
            status, msg_data = self.connection.fetch(email_id, "(RFC822)")

            if status != "OK":
                return {}

            # Parse the email
            msg = email.message_from_bytes(msg_data[0][1])

            # Decode subject
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode(errors="replace")

            # Get sender
            from_addr = msg.get("From")

            # Get date
            date = msg.get("Date")

            body = self._extract_text_body(msg)

            return {
                "id": email_id.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date,
                "body": body,
            }

        except Exception as e:
            logger.error(f"Failed to fetch email details: {str(e)}")
            return {}
    def _extract_password_from_body(self, body_text: str) -> str | None:
        """
        Extracts a password value from body text like: 'password: 322792'
        Returns the first match or None.
        """
        if not body_text:
            return None

        match = re.search(r"(?im)^\s*password\s*:\s*([0-9]+)\s*$", body_text)
        if match:
            return match.group(1)

        # Slightly more permissive fallback (in case it's not on its own line)
        match = re.search(r"(?i)\bpassword\s*:\s*([0-9]+)\b", body_text)
        return match.group(1) if match else None
    def _extract_https_link_from_body(self, body_text: str) -> str | None:
        """Extract the first https:// link from body text (if present)."""
        if not body_text:
            return None

        # Take the first https URL and stop at whitespace or common trailing punctuation.
        match = re.search(r"https://[^\s<>()\"']+", body_text, flags=re.IGNORECASE)
        if not match:
            return None

        url = match.group(0)
        return url.rstrip(".,;:!?)\"]'")
    def get_email_password(self, email_id: bytes) -> str | None:
        """Fetch an email and extract the password from its body (if present)."""
        details = self.get_email_details(email_id)
        body_text = (details.get("body") or "")
        return self._extract_password_from_body(body_text)
    def get_email_link(self, email_id: bytes) -> str | None:
        """Fetch an email and extract the first https link from its body (if present)."""
        details = self.get_email_details(email_id)
        body_text = (details.get("body") or "")
        return self._extract_https_link_from_body(body_text)
    def search_emails(self, search_string: str) -> list[bytes]:
        """Search for emails by date + subject and return their IMAP IDs (bytes)."""
        if not self.connection:
            logger.error("Not connected. Call connect() first.")
            return []

        try:
            # Select INBOX
            self.connection.select("INBOX")

            # IMAP search (server-side)
            safe_search = search_string.replace('"', '\\"')
            status, message_ids = self.connection.search(
                None,
                "ON", DATE_TODAY,
                "SUBJECT", f'"{safe_search}"',
            )

            if status != "OK":
                logger.error("Search failed")
                return []

            email_ids = message_ids[0].split()

            if email_ids:
                logger.info(f"✓ Found {len(email_ids)} email(s) containing '{search_string}'")
            else:
                logger.info(f"No emails found containing '{search_string}'")

            return email_ids

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []


def main():
    """Search for emails containing 'Audiente'."""

    email_service = EmailService()

    if not email_service.connect():
        logger.error("Failed to connect")
        return

    # Search for emails with "Audiente"
    email_ids = email_service.search_emails(DATE_OF_DATA)

    if email_ids:
        logger.info(f"\nFound {len(email_ids)} matching email(s):")
        logger.info("-" * 50)

        # Get details for each email
        for email_id in email_ids:
            details = email_service.get_email_details(email_id)
            if details:
                logger.info(f"Subject: {details['subject']}")
                logger.info(f"From: {details['from']}")
                logger.info(f"Date: {details['date']}")

                link = email_service.get_email_link(email_id)
                logger.info(f"Link: {link if link else '(not found)'}")

                pwd = email_service.get_email_password(email_id)
                logger.info(f"Password: {pwd if pwd else '(not found)'}")

                logger.info("-" * 50)

    email_service.disconnect()


if __name__ == "__main__":
    main()