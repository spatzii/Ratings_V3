from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass()
class RequestParams:
    """
A dataclass that handles parameters for rating file requests and time range calculations.

This class encapsulates parameters received via HTTP requests from the front-end,
providing structured access to date components and utility methods for path construction,
time range formatting and selected channels.

Attributes:
    year (str): The year component in YYYY format
    month (str): The month component in MM format
    day (str): The day component in DD format
    start_hour (str): Starting hour in HH format
    end_hour (str): Ending hour in HH format
    channels (str | list[str]): Channels in string format

Properties:
    file_path: Constructs a storage path in the format "YYYY/MM/YYYY-MM-DD.json"

    time_range: Returns a tuple of formatted time strings (HH:MM, HH:MM), with end_hour
               adjusted by -1 minute to match rating reading intervals

Example:
    >>> params = RequestParams("2025", "05", "17", "20", "23", 'Digi 24,Antena 3 CNN')
    >>> params.file_path
    '2025/05/2025-05-17.json'
    >>> params.time_range
    ('20:00', '22:59')
    >>> params.channels
    ['Digi 24', 'Antena 3 CNN']
"""

    year: str
    month: str
    day: str
    start_hour:str
    end_hour:str
    channels: str | list[str]

    def __post_init__(self):
        """Makes the dataclass accept either string (via HTTP request)
        or list of strings (in which case __post_init__ is passed).
        If input is string, transforms to list.

        Example:
            channels:str = 'Digi 24,Antena 3 CNN'
            channels:list[str] = ['Digi 24', 'Antena 3 CNN']
        """
        if isinstance(self.channels, str):
            self.channels = [c.strip() for c in self.channels.split(',')]

    @property
    def file_path(self) -> str:
        return f"{self.year}/{self.month}/{self.year}-{self.month}-{self.day}.json"

    @property
    def time_range(self) -> tuple[str, str]:
        self.start_hour = datetime.strptime(self.start_hour, format('%H')).strftime('%H:%M')

        ### Remove 1 minute from incoming end_hour so it matches rating reading
        # i.e. from 20:00 to 22:59, not 20:00 to 23:00.
        self.end_hour = (datetime.strptime(self.end_hour, format('%H')) - timedelta(hours=0, minutes=1)).strftime('%H:%M')

        return self.start_hour, self.end_hour