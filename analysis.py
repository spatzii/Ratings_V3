import pandas as pd
import json

from utils import read_json

def ratings_read_test(file):
    jds = read_json(file)
    resampled_data = jds.loc['2025-05-07 20:00':'2025-05-07 22:59',
                            ['Digi 24', 'Antena 3 CNN']].resample('15min').mean().round(2)
    mean_data = jds.loc['2025-05-07 20:00':'2025-05-07 22:59',
                ['Digi 24', 'Antena 3 CNN']].mean().round(2)

    resampled_dict = {}
    for column in resampled_data.columns:
        resampled_dict[column] = {index.strftime('%Y-%m-%d %H:%M:%S'): value
                                  for index, value in resampled_data[column].items()}

    result = {
        "resampled_data": resampled_dict,
        "mean_data": mean_data.to_dict()
    }
    # print(result)
    return json.dumps(result)


    # print(jds.loc['2025-05-07 20:00':'2025-05-07 22:59', ['Digi 24', 'Antena 3 CNN']].resample('15min').mean().round(2))
    # print("\n")
    # print(jds.loc['2025-05-07 20:00':'2025-05-07 22:59', ['Digi 24', 'Antena 3 CNN']].mean().round(2))
