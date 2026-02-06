import json
from pathlib import Path


class MockCredentialsService:
    """Mock service that reads credentials from Data/mock.json for development."""

    def __init__(self):
        self.mock_file = Path(__file__).parent.parent / "Data" / "mock.json"

    def fetch_ratings_credentials(self) -> tuple[str, str] | None:
        """Return (password, link) from mock.json."""
        with open(self.mock_file, "r") as f:
            data = json.load(f)

        creds = data.get("test_credentials", {})
        password = creds.get("password")
        link = creds.get("link")

        if password and link:
            return password, link
        return None
