import pandas as pd
import json

from utils import unpack_json_to_dataframe


def ratings_read_test(file):
    ratings = unpack_json_to_dataframe(file)
    jds = ratings.between_time('20:00', '22:59')
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

    result = resampled_dict
    return json.dumps(result)

    # print(jds.loc['2025-05-07 20:00':'2025-05-07 22:59', ['Digi 24', 'Antena 3 CNN']].resample('15min').mean().round(2))
    # print("\n")
    # print(jds.loc['2025-05-07 20:00':'2025-05-07 22:59', ['Digi 24', 'Antena 3 CNN']].mean().round(2))
