from utils.config import current_config
from datetime import datetime
from utils.logger import get_logger
from pathlib import Path

logger = get_logger(__name__)

class StorageService:

    def __init__(self, filename):
        self.filename = filename

    def extract_date(self) -> tuple[str, str, str]:
        """Extract year, month, day from the filename in YYYY-MM-DD format."""
        date_str = str(self.filename).split(' ')[-1].replace('.xlsx', '')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return (str(date_obj.year),
                f"{date_obj.month:02d}",
                f"{date_obj.day:02d}")

    def _generate_storage_path(self) -> str:
        year, month, day = self.extract_date()
        return f"{year}/{month}/{year}-{month}-{day}.json"

    def storage_path(self) -> str:
        return self._handle_storage_path(self._generate_storage_path())

    @staticmethod
    def _handle_storage_path(base_path: str) -> str:
        """Handle storage-specific path operations

        Example:
            >>> received_path = ...

        """
        if current_config.STORAGE_TYPE == 'local':
            full_path: Path = Path(f"{current_config.STORAGE_PATH}/{base_path}")
            if full_path.exists():
                logger.info(f"File {full_path} already exists, skipping...")
                return str(full_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            return str(full_path)
        else:  # firebase
            return f"{current_config.STORAGE_PATH}/{base_path}"

