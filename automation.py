#!/usr/bin/env python3
"""
Daily Ratings Automation Script
Designed to run via cron between 8:30 AM - 8:45 AM

This script:
1. Checks for today's ratings email
2. If not found, waits and retries (with safe API rate limiting)
3. Downloads the ratings file
4. Generates HTML report
5. Emails the report to recipients
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

from services.daily_report_generator import DailyReportGenerator
from services.email_service import ExtractionError
from utils.config import current_config
from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
MAX_RETRIES = 20  # Maximum number of retry attempts
RETRY_INTERVAL = 60  # Seconds between retries (1 minute is safe for Gmail API)
REPORT_RECIPIENTS = [
    "pana.stefan@gmail.com",
    "citre.cristian@gmail.com"
]


def check_if_already_processed_today() -> bool:
    """Check if we've already processed today's file.

    Returns:
        True if today's file exists in download directory
    """
    today = datetime.now().strftime("%Y-%m-%d")
    expected_filename = f"Digi 24-audiente zilnice la minut {today}.xlsx"
    filepath = current_config.DOWNLOAD_DIR / expected_filename

    if filepath.exists():
        logger.info(f"Today's file already exists: {filepath.name}")
        return True
    return False


async def attempt_download() -> Path | None:
    """Attempt to fetch credentials and download ratings file.

    Returns:
        Path to downloaded file if successful, None if email not yet arrived

    Raises:
        ExtractionError: If email found but credentials invalid
        Exception: For other download failures
    """
    # Try today's email first
    logger.info("Checking for today's ratings email...")
    email_service = current_config.get_credentials_service(use_yesterday=False)

    credentials = email_service.fetch_ratings_credentials()

    if credentials is None:
        logger.info("Today's email hasn't arrived yet")
        return None

    password, link = credentials
    logger.info(f"✓ Found credentials - Password: {password}")

    # Download the file
    downloader = current_config.get_downloader()
    filepath = downloader.download(password, link)

    if filepath is None:
        raise Exception("Download failed despite having valid credentials")

    logger.info(f"✓ Downloaded: {filepath.name}")
    return filepath


async def generate_and_send_report(filepath: Path) -> None:
    """Generate HTML report and email it to recipients.

    Args:
        filepath: Path to the downloaded ratings file
    """
    logger.info("Generating ratings report...")

    report_generator = DailyReportGenerator(
        filepath=filepath,
        channels=['Digi 24', 'Antena 3 CNN'],
        include_slot_averages=True
    )

    report = await report_generator.generate_report()
    html_report = report_generator.to_html(report)

    logger.info("Sending reports to recipients...")

    # Send to all recipients
    email_service = current_config.get_credentials_service()
    for recipient in REPORT_RECIPIENTS:
        try:
            email_service.send_report(html_report, recipient)
            logger.info(f"✓ Sent report to {recipient}")
        except Exception as e:
            logger.error(f"✗ Failed to send to {recipient}: {str(e)}")


async def main():
    """Main execution flow with retry logic."""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Daily Ratings Automation Started - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # Check if we've already processed today
    if check_if_already_processed_today():
        logger.info("Today's ratings already processed. Exiting.")
        return 0

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"\nAttempt {attempt}/{MAX_RETRIES}")

        try:
            filepath = await attempt_download()

            if filepath:
                # Success! Generate and send report
                await generate_and_send_report(filepath)

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info("=" * 80)
                logger.info(f"✓ SUCCESS - Completed in {elapsed:.1f} seconds")
                logger.info("=" * 80)
                return 0

            # Email hasn't arrived yet
            if attempt < MAX_RETRIES:
                logger.info(f"Waiting {RETRY_INTERVAL} seconds before retry...")
                time.sleep(RETRY_INTERVAL)
            else:
                logger.error("Max retries reached. Email hasn't arrived.")
                return 1

        except ExtractionError as e:
            logger.error(f"Credential extraction failed: {str(e)}")
            return 2

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}: {str(e)}", exc_info=True)

            if attempt < MAX_RETRIES:
                logger.info(f"Waiting {RETRY_INTERVAL} seconds before retry...")
                time.sleep(RETRY_INTERVAL)
            else:
                logger.error("Max retries reached with errors.")
                return 3

    return 4  # Should never reach here


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
