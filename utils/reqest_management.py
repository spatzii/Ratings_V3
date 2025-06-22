from dataclasses import dataclass
from datetime import datetime, timedelta
from utils.config import current_config
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

    time_range: Returns a list of formatted time strings [HH:MM, HH:MM]

Example:
    >>> params = RequestParams("2025", "05", "17", "20", "23", 'Digi 24,Antena 3 CNN')
    >>> params.request_date
    '2025/05/2025-05-17'
    >>> params.time_range
    ['20:00', '23:00']
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
    def request_date(self) -> str:
        return f"{self.year}-{self.month}-{self.day}"

    @property
    def time_range(self) -> list[str]:
        self.start_hour = datetime.strptime(self.start_hour, format('%H')).strftime('%H:%M')
        self.end_hour = datetime.strptime(self.end_hour, format('%H')).strftime('%H:%M')

        return [self.start_hour, self.end_hour]

    @classmethod
    async def from_query(cls,
                         year: str,
                         month: str,
                         day: str,
                         startHour: str,
                         endHour: str,
                         channels: str
                         ) -> "RequestParams":
        return cls(
            year=year,
            month=month,
            day=day,
            start_hour=startHour,
            end_hour=endHour,
            channels=channels
        )
