import pandas as pd
import json

from xlsx_to_json import json_to_df


def read_ratings(file_path:str, time_range:tuple[str, str]) -> str:
    ratings_data:pd.DataFrame = json_to_df(file_path)
    timeframe:pd.DataFrame = ratings_data.between_time(time_range[0], time_range[1])
    resampled_data = timeframe.loc[:,
                            ['Digi 24', 'Antena 3 CNN']].resample('15min').mean().round(2)
    mean_data = timeframe.loc[:,
                ['Digi 24', 'Antena 3 CNN']].mean().round(2)

    resampled_dict = {}
    for column in resampled_data.columns:
        # Create dictionary for each column including both resampled and mean data
        column_data = {index.strftime('%Y-%m-%d %H:%M:%S'): value
                      for index, value in resampled_data[column].items()}
        # Add mean value as the last entry with a special timestamp
        column_data['Medie'] = mean_data[column]
        resampled_dict[column] = column_data

    result:dict = resampled_dict
    return json.dumps(result)
