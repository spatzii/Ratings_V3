"""Stub implementation of EmailService for testing."""

import json
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


class StubEmailService:
    """Stub EmailService that returns data from scenario configuration.

    Usage:
        stub = StubEmailService.from_scenario_file(
            "Data/test_scenarios/scenarios.json",
            "happy_path"
        )
        credentials = stub.fetch_ratings_credentials()
    """

    def __init__(self, scenario: dict):
        """Initialize with a scenario dict.

        Args:
            scenario: Single scenario dict containing 'email', 'download', etc.
        """
        self.scenario = scenario
        self.email_config = scenario.get("email", {})

        # Track calls for test assertions
        self._fetch_credentials_calls = []
        self._send_report_calls = []

    @classmethod
    def from_scenario_file(cls, file_path: str | Path, scenario_name: str) -> "StubEmailService":
        """Load a specific scenario from a scenarios JSON file.

        Args:
            file_path: Path to scenarios.json
            scenario_name: Name of the scenario to load (e.g., "happy_path")

        Returns:
            StubEmailService configured with the specified scenario

        Raises:
            ValueError: If scenario_name not found in file
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        with open(file_path) as f:
            data = json.load(f)

        scenarios = data.get("scenarios", [])

        for scenario in scenarios:
            if scenario.get("name") == scenario_name:
                logger.info(f"Loaded scenario: {scenario_name}")
                return cls(scenario)

        available = [s.get("name") for s in scenarios]
        raise ValueError(f"Scenario '{scenario_name}' not found. Available: {available}")

    def fetch_ratings_credentials(self) -> tuple[str, str] | None:
        """Return credentials based on scenario configuration.

        Returns:
            tuple[str, str] | None: (password, link) if available, None otherwise
        """
        self._fetch_credentials_calls.append({
            "scenario": self.scenario.get("name")
        })

        # Email hasn't arrived
        if not self.email_config.get("email_found", True):
            logger.info("Ratings email hasn't arrived yet")
            return None

        # Delay announced
        if self.email_config.get("delay_announced"):
            delay_msg = self.email_config.get("delay_message", "Ratings will be delayed")
            logger.info(f"Delay announced: {delay_msg}")
            return None

        # Extract credentials
        password = self.email_config.get("password")
        link = self.email_config.get("link")

        # Missing password or link
        if not password:
            logger.warning("No password found in email")
            return None

        if not link:
            logger.warning("No link found in email")
            return None

        logger.info(f"Password: {password}")
        logger.info(f"Link: {link}")
        return password, link

    def send_report(self, report_html: str, recipient: str) -> None:
        """Log report sending instead of actually sending.

        Args:
            report_html: The HTML content of the report
            recipient: The email address to send to
        """
        self._send_report_calls.append({
            "recipient": recipient,
            "html": report_html,
            "html_length": len(report_html)
        })
        logger.info(f"[STUB] Would send report ({len(report_html)} chars) to {recipient}")

    @property
    def fetch_credentials_calls(self) -> list[dict]:
        """Access recorded fetch_ratings_credentials calls."""
        return self._fetch_credentials_calls

    @property
    def send_report_calls(self) -> list[dict]:
        """Access recorded send_report calls."""
        return self._send_report_calls

    def reset_call_tracking(self) -> None:
        """Clear all recorded calls."""
        self._fetch_credentials_calls = []
        self._send_report_calls = []
