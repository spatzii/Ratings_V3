import pandas as pd
import json

from xlsx_to_json import json_to_df


def read_ratings(filepath:str) -> str:
    ratings_data:pd.DataFrame = json_to_df(filepath)
    jds:pd.DataFrame = ratings_data.between_time('20:00', '22:59')
    resampled_data = jds.loc[:,
                            ['Digi 24', 'Antena 3 CNN']].resample('15min').mean().round(2)
    mean_data = jds.loc[:,
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
