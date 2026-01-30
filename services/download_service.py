import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# ============ CONFIG ============
DOWNLOAD_DIR = Path("/Users/stefanpana/PycharmProjects/RatingsBackend")
BACKEND_URL = "http://localhost:8000/api/v1/upload/xlsx"  # Updated to match your FastAPI endpoint
DOWNLOAD_DATE = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")  # e.g. 2026-01-28


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

            # 1. Follow short URL to get the UUID
            logger.info(f"Following redirect: {short_url}")
            resp = session.get(short_url, allow_redirects=True, timeout=10)
            resp.raise_for_status()

            # Extract UUID from final URL
            final_url = resp.url
            logger.info(f"Final URL: {final_url}")

            if '/links/' not in final_url:
                logger.error(f"Unexpected URL format: {final_url}")
                return None

            uuid = final_url.split('/links/')[1].split('/')[0].split('?')[0]
            storage_url = f"https://storage.rcs-rds.ro/links/{uuid}"
            logger.info(f"✓ Extracted UUID: {uuid}")

            # 2. Construct filename
            filename = f"Digi 24-audiente zilnice la minut {DOWNLOAD_DATE}.xlsx"
            logger.info(f"Target file: {filename}")

            # 3. Build download URL with password parameter
            download_url = (
                f"https://storage.rcs-rds.ro/content/links/{uuid}/files/get/"
                f"{requests.utils.quote(filename)}"
                f"?path=%2F{requests.utils.quote(filename)}&password={password}"
            )

            # 4. Set headers to mimic browser (CRITICAL for success!)
            headers = {
                'Referer': storage_url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }

            # 5. Download the file
            logger.info("Downloading file...")
            resp = session.get(download_url, headers=headers, timeout=30)
            resp.raise_for_status()

            # 6. Verify we got a real file, not an error page
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.error(f"Got HTML response instead of file. Content-Type: {content_type}")
                logger.error(f"Response preview: {resp.text[:500]}")
                return None

            # 7. Verify file size is reasonable (should be ~1.5-2 MB)
            file_size_mb = len(resp.content) / 1024 / 1024
            if file_size_mb < 0.5:
                logger.error(f"Downloaded file is too small ({file_size_mb:.2f} MB), likely an error")
                return None

            # 8. Save file
            filepath = self.download_dir / filename
            filepath.write_bytes(resp.content)
            logger.info(f"✓ Downloaded: {filepath.name} ({file_size_mb:.2f} MB)")

            return filepath

        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {str(e)}")
            if 'resp' in locals():
                logger.error(f"Response status: {resp.status_code}")
                if hasattr(resp, 'text') and resp.text:
                    logger.error(f"Response preview: {resp.text[:500]}")
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
                files = {'xlsx_file': (filepath.name, f,
                                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                resp = requests.post(self.backend_url, files=files, timeout=30)
                resp.raise_for_status()

            logger.info(f"✓ Uploaded: {filepath.name}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Upload failed: {str(e)}")
            if 'resp' in locals():
                logger.error(f"Response status: {resp.status_code}")
                if hasattr(resp, 'text') and resp.text:
                    logger.error(f"Response: {resp.text[:500]}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False


def main():
    """Main entry point: fetch credentials and download ratings file.

    For testing, you can use MockCredentialsService instead of EmailService.
    """
    logger.info("Starting ratings download automation...")

    # For production, use EmailService
    # from services.email_service import EmailService
    # credentials_service = EmailService()

    # For testing, use MockCredentialsService
    from services.mock_credentials import MockCredentialsService
    credentials_service = MockCredentialsService()

    credentials = credentials_service.fetch_ratings_credentials()

    if not credentials:
        logger.error("Failed to retrieve credentials")
        return False

    password, short_url = credentials
    logger.info(f"✓ Got credentials")
    logger.info(f"  Password: {password}")
    logger.info(f"  Link: {short_url}")

    # Download the file
    downloader = RatingsDownloader()
    filepath = downloader.download(password, short_url)

    if not filepath:
        logger.error("Failed to download file")
        return False

    # Upload to backend
    if not downloader.upload_to_backend(filepath):
        logger.error("Failed to upload file to backend")
        return False

    logger.info("✓ Download and upload complete!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)