from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass()
class RatingsParams:
    """Dataclass that contains the information relating to the rating file request received via HTTP from the front-end:

    - a date that constructs a path for storage

    - a timeframe for constructing DataFrame
    """
    year: str
    month: str
    day: str
    start_hour:str
    end_hour:str

    @property
    def file_path(self) -> str:
        return f"{self.year}/{self.month}/{self.year}-{self.month}-{self.day}.json"

    @property
    def time_range(self) -> tuple[str, str]:
        self.start_hour = datetime.strptime(self.start_hour, format('%H')).strftime('%H:%M')

        ### Remove 1 minute from incoming end_hour so it matches rating reading i.e. from 20:00 to 22:59, not 20:00 to 23:00.
        self.end_hour = (datetime.strptime(self.end_hour, format('%H')) - timedelta(hours=0, minutes=1)).strftime('%H:%M')

        return self.start_hour, self.end_hour