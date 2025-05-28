from dataclasses import dataclass
@dataclass()
class RatingsParams:
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
        return self.start_hour, self.end_hour