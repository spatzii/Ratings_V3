import imaplib
import email
import os
import datetime

from email.header import decode_header
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

DATE_TODAY = datetime.datetime.today().strftime("%d-%b-%Y") # IMAP formatting, eg. 01-Jan-2026
DATE_OF_DATA = (datetime.datetime.today() - timedelta(days=1)).strftime("%d.%m") # Digi email format eg. 01.01.
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

    def search_emails(self, search_string: str) -> list:
        """Search for emails containing a specific string in subject or body.

        Args:
            search_string: String to search for (e.g., "Audiente")

        Returns:
            list: List of email IDs that match the search
        """
        if not self.connection:
            logger.error("Not connected. Call connect() first.")
            return []

        try:
            # Select INBOX
            self.connection.select("INBOX")

            # Search for emails with the string in subject
            # You can also search in body with BODY, or use OR for both
            status, message_ids = self.connection.search(
                None,
                "ON", DATE_TODAY,
                "SUBJECT", f'"{search_string}"',
            )

            if status != "OK":
                logger.error("Search failed")
                return []

            # message_ids[0] is a space-separated string of IDs
            email_ids = message_ids[0].split()

            if email_ids:
                logger.info(f"✓ Found {len(email_ids)} email(s) containing '{search_string}'")
            else:
                logger.info(f"No emails found containing '{search_string}'")

            return email_ids

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def get_email_details(self, email_id: bytes) -> dict:
        """Fetch basic details of an email.

        Args:
            email_id: Email ID from search results

        Returns:
            dict: Email details (subject, from, date)
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
                subject = subject.decode()

            # Get sender
            from_addr = msg.get("From")

            # Get date
            date = msg.get("Date")

            return {
                "id": email_id.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date
            }

        except Exception as e:
            logger.error(f"Failed to fetch email details: {str(e)}")
            return {}



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
                logger.info("-" * 50)

    email_service.disconnect()


if __name__ == "__main__":
    main()