from utils.supabase_init import supabase as db
from utils.logger import get_logger
from postgrest import APIResponse
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

logger = get_logger(__name__)

RATINGS_TABLE = db.table('tv_ratings')
INDEX = 'Timebands'
RESAMPLE_INTERVAL = '15min'
DECIMAL_PRECISION = 2

class DatabaseService:

    def __init__(self, daily_ratings:dict):
        self.daily_ratings = daily_ratings.get('data')

    def insert_tv_ratings(self):
        RATINGS_TABLE.insert(self.daily_ratings).execute()
        logger.info("Insert successful!")


class RatingsTable:
    """Class for handling TV ratings database queries and response processing."""

    def __init__(self, df: pd.DataFrame):
        """Initialize with a pre-processed DataFrame.

        Args:
            df: Preprocessed DataFrame with ratings data
        """
        self._dataframe = df

    @classmethod
    def from_timeframe(cls, date: str, timeframe: List[str], channels: List[str]) -> 'RatingsTable':
        """Factory method to create instance from timeframe and channels.

        Args:
            timeframe: List containing start and end times
            channels: List of channel names to query

        Returns:
            DatabaseResponse instance

        Raises:
            ValueError: If timeframe or channels are invalid
            :param channels:
            :param timeframe:
            :param date:
        """

        start_time = pd.to_datetime(date + " " + timeframe[0])
        end_time = pd.to_datetime(date + " " + timeframe[1])


        prepared_channels = cls._prepare_channels(channels)
        sql_channels = cls._format_channels_for_query(prepared_channels)

        try:
            data = cls._fetch_ratings(start_time, end_time, sql_channels)
            df = cls._create_dataframe(data)
            return cls(df)
        except Exception as e:
            logger.error(f"Error fetching ratings data: {str(e)}")
            raise

    @staticmethod
    def _prepare_channels(channels: List[str]) -> List[str]:
        """Prepare channel list by ensuring Timebands is first and only appears once."""
        channels_without_timebands = [c for c in channels if c != "Timebands"]
        return ["Timebands"] + channels_without_timebands

    @staticmethod
    def _format_channels_for_query(channels: List[str]) -> str:
        """Format channel names for SQL query."""
        return ', '.join(f'"{channel}"' for channel in channels)

    @classmethod
    def _fetch_ratings(cls, start_time: datetime, end_time: datetime, sql_channels: str) -> List[Dict]:
        """Fetch ratings data from database.

        Args:
            start_time: Start timestamp
            end_time: End timestamp
            sql_channels: Formatted channel names for query

        Returns:
            List of rating records
        """
        try:
            response: APIResponse = (RATINGS_TABLE
                                     .select(sql_channels)
                                     .gte(INDEX, str(start_time))
                                     .lt(INDEX, str(end_time))
                                     .execute())
            return response.data
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            raise

    @classmethod
    def _create_dataframe(cls, data: List[Dict]) -> pd.DataFrame:
        """Create and prepare DataFrame from raw data.

        Args:
            data: List of rating records

        Returns:
            Processed DataFrame
        """
        df = pd.DataFrame(data)
        df.set_index(INDEX, inplace=True)
        df.index = pd.to_datetime(df.index)
        return df

    def basetable(self) -> pd.DataFrame:
        """Calculate and return interval and overall averages.

        Returns:
            DataFrame with resampled averages and overall average
        """
        interval_avg = self._dataframe.mean().round(DECIMAL_PRECISION)
        interval_avg = pd.DataFrame(interval_avg).T
        interval_avg.index = ['Average']

        quarter_avg = self._dataframe.resample(RESAMPLE_INTERVAL).mean().round(DECIMAL_PRECISION)
        quarter_avg = self.rename_index(quarter_avg)

        return pd.concat([quarter_avg, interval_avg])

    @property
    def raw_data(self) -> pd.DataFrame:
        """Return the raw DataFrame.

        Returns:
            Raw ratings DataFrame
        """
        # return self._dataframe.copy()
        return self._dataframe.resample(RESAMPLE_INTERVAL).mean().round(DECIMAL_PRECISION)

    @staticmethod
    def rename_index(df: pd.DataFrame) -> pd.DataFrame:
        """Renames time columns to reflect 15 minute intervals"""
        # Get times using datetime properties instead of strftime
        time_only = [idx.strftime('%H:%M') for idx in df.index]

        # Create new labels with 15-min intervals
        new_labels = []
        for start in time_only:
            end_dt = pd.to_datetime(start, format='%H:%M') + pd.Timedelta(minutes=15)
            new_labels.append(f"{start} - {end_dt.strftime('%H:%M')}")

        df.index = new_labels
        return df

