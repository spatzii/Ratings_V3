"""Stub implementation of RatingsDownloader for testing."""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class StubDownloader:
    """Stub RatingsDownloader that copies test files instead of downloading.

    Usage:
        stub = StubDownloader.from_scenario_file(
            "Data/test_scenarios/scenarios.json",
            "happy_path",
            download_dir=Path("Data/test_downloads")
        )
        filepath = stub.download("123456", "https://s.go.ro/abc")
    """

    # Default location for test xlsx files
    DEFAULT_TEST_FILES_DIR = Path(__file__).parent.parent / 'Data' / 'test_files'

    def __init__(
        self,
        scenario: dict,
        download_dir: Path,
        test_files_dir: Path = None
    ):
        """Initialize with a scenario dict.

        Args:
            scenario: Single scenario dict containing 'download' config
            download_dir: Where to "download" (copy) files to
            test_files_dir: Where test xlsx files are stored
        """
        self.scenario = scenario
        self.download_config = scenario.get("download", {})
        self.download_dir = Path(download_dir)
        self.test_files_dir = Path(test_files_dir) if test_files_dir else self.DEFAULT_TEST_FILES_DIR

        # Ensure download dir exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Track calls for test assertions
        self._download_calls = []

    @classmethod
    def from_scenario_file(
        cls,
        file_path: str | Path,
        scenario_name: str,
        download_dir: Path,
        test_files_dir: Path = None
    ) -> "StubDownloader":
        """Load a specific scenario from a scenarios JSON file.

        Args:
            file_path: Path to scenarios.json
            scenario_name: Name of the scenario to load
            download_dir: Where to "download" files to
            test_files_dir: Where test xlsx files are stored

        Returns:
            StubDownloader configured with the specified scenario
        """
        file_path = Path(file_path)

        with open(file_path) as f:
            data = json.load(f)

        scenarios = data.get("scenarios", [])

        for scenario in scenarios:
            if scenario.get("name") == scenario_name:
                logger.info(f"Loaded download scenario: {scenario_name}")
                return cls(scenario, download_dir, test_files_dir)

        available = [s.get("name") for s in scenarios]
        raise ValueError(f"Scenario '{scenario_name}' not found. Available: {available}")

    def download(
        self,
        password: str,
        short_url: str,
        download_date: Optional[str] = None
    ) -> Optional[Path]:
        """Simulate download by copying a test file.

        Args:
            password: Password (logged but not used)
            short_url: URL (logged but not used)
            download_date: Optional date for filename

        Returns:
            Path to copied file if scenario.download.success is True, None otherwise
        """
        self._download_calls.append({
            "password": password,
            "short_url": short_url,
            "download_date": download_date,
            "scenario": self.scenario.get("name")
        })

        # Check if download should succeed
        if not self.download_config.get("success", True):
            error_msg = self.download_config.get("error_message", "Download failed")
            logger.error(f"[STUB] {error_msg}")
            return None

        # Get source test file
        source_filename = self.download_config.get("file", "sample_ratings.xlsx")
        source_path = self.test_files_dir / source_filename

        if not source_path.exists():
            logger.error(f"[STUB] Test file not found: {source_path}")
            return None

        # Determine target filename (matches real downloader behavior)
        effective_date = download_date or (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        target_filename = f"Digi 24-audiente zilnice la minut {effective_date}.xlsx"
        target_path = self.download_dir / target_filename

        # Copy file
        shutil.copy2(source_path, target_path)
        file_size_mb = target_path.stat().st_size / 1024 / 1024

        logger.info(f"[STUB] Copied test file: {source_filename} -> {target_filename}")
        logger.info(f"[STUB] Downloaded: {target_path.name} ({file_size_mb:.2f} MB)")

        return target_path

    @property
    def download_calls(self) -> list[dict]:
        """Access recorded download calls."""
        return self._download_calls

    def reset_call_tracking(self) -> None:
        """Clear all recorded calls."""
        self._download_calls = []
