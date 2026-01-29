import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from services.email_service import EmailService
from utils.logger import get_logger

logger = get_logger(__name__)

# ============ CONFIG ============
DOWNLOAD_DIR = Path("/Users/stefanpana/PycharmProjects/RatingsBackend")
BACKEND_URL = "http://localhost:5000/upload"
DOWNLOAD_DATE = (datetime.today()-timedelta(days=1)).strftime("%Y-%m-%d")  # e.g. 2026-01-28

class RatingsDownloader:
    """Downloads TV ratings files from Digi Storage using credentials from EmailService."""

    def __init__(self, download_dir: Path = DOWNLOAD_DIR, backend_url: str = BACKEND_URL):
        """Initialize the downloader with target directories.

        Args:
            download_dir: Path where xlsx files will be saved
            backend_url: Backend API endpoint for uploading files
        """
        self.download_dir = download_dir
        self.backend_url = backend_url
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download(self, password: str, short_url: str) -> Optional[Path]:
        """Download ratings file from Digi Storage.

        Args:
            password: Password extracted from email
            short_url: Short URL (https://s.go.ro/xxxxx) from email

        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            session = requests.Session()

            # 1. Follow short URL to get the real Digi Storage link and UUID
            logger.info(f"Following redirect: {short_url}")
            resp = session.get(short_url, allow_redirects=True, timeout=10)
            resp.raise_for_status()

            uuid = resp.url.split('/links/')[-1].split('?')[0]
            logger.info(f"✓ Extracted UUID: {uuid}")

            # 2. Submit password (may set auth cookie)
            logger.info("Submitting password...")
            session.post(
                f"https://storage.rcs-rds.ro/links/{uuid}",
                data={"password": password},
                timeout=10
            )

            # 3. Construct today's filename
            filename = f"Digi 24-audiente zilnice {DOWNLOAD_DATE}.xlsx"
            logger.info(f"Looking for file: {filename}")

            # 4. Direct download with password in URL
            download_url = (
                f"https://storage.rcs-rds.ro/content/links/{uuid}/files/get/"
                f"{requests.utils.quote(filename)}"
                f"?path=%2F{requests.utils.quote(filename)}&password={password}"
            )

            logger.info("Downloading file...")
            resp = session.get(download_url, timeout=30)
            resp.raise_for_status()

            # 5. Save file
            filepath = self.download_dir / filename
            filepath.write_bytes(resp.content)
            logger.info(f"✓ Downloaded: {filepath.name} ({len(resp.content) / 1024 / 1024:.2f} MB)")

            return filepath

        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def upload_to_backend(self, filepath: Path) -> bool:
        """Upload downloaded file to backend API.

        Args:
            filepath: Path to the xlsx file

        Returns:
            True if upload successful, False otherwise
        """
        try:
            logger.info(f"Uploading to backend: {self.backend_url}")
            with open(filepath, 'rb') as f:
                files = {'xlsx_file': f}
                resp = requests.post(self.backend_url, files=files, timeout=30)
                resp.raise_for_status()

            logger.info(f"✓ Uploaded: {filepath.name}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Upload failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False


def main():
    """Main entry point: fetch credentials from email and download ratings file."""
    logger.info("Starting ratings download automation...")

    # 1. Get credentials from email
    email_service = EmailService()
    credentials = email_service.fetch_ratings_credentials()

    if not credentials:
        logger.error("Failed to retrieve credentials from email")
        return False

    password, short_url = credentials
    logger.info(f"✓ Got credentials from email")

    # 2. Download the file
    downloader = RatingsDownloader()
    filepath = downloader.download(password, short_url)

    if not filepath:
        logger.error("Failed to download file")
        return False

    # 3. Upload to backend
    if not downloader.upload_to_backend(filepath):
        logger.error("Failed to upload file to backend")
        return False

    logger.info("✓ Download and upload complete!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)