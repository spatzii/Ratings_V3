import pandas as pd
import json

from xlsx_to_json import json_to_df
from utils.utils_analysis import create_dataframe_dict

RESAMPLE_INTERVAL = '15min'
DECIMAL_PRECISION = 2

def read_custom_ratings(file_path:str, time_range:tuple[str, str], channels:list[str]) -> str:
    """Process custom ratings data from a file for specified channels and time range.

    Args:
        file_path: Path to the input file
        time_range: Tuple of (start_time, end_time) in string format
        channels: List of channel names to process

    Returns:
        JSON string containing processed ratings data with resampled and mean values

    Example:
        >>> read_custom_ratings("ratings.json", ("08:00", "17:00"), ["channel1", "channel2"])
    """

    # Creates a Pandas DataFrame object #
    ratings_data:pd.DataFrame = json_to_df(file_path)
    # Refines DataFrame to a specific timeframe: start hour and end hour
    timeframe:pd.DataFrame = ratings_data.between_time(time_range[0], time_range[1])
    # Creates 15-min averages inside the timeframe, corresponding to how ratings are read
    resampled_data:pd.DataFrame = timeframe.loc[:, channels].resample(RESAMPLE_INTERVAL).mean().round(DECIMAL_PRECISION)
    # Creates an average for the entire timeframe
    mean_data = timeframe.loc[:, channels].mean().round(DECIMAL_PRECISION)
    # Returns json string object with dictionary of values
    return json.dumps(create_dataframe_dict(resampled_data, mean_data))
