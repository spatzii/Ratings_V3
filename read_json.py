import pandas as pd
import json


def read_json(json_str):
    dataframe = pd.DataFrame(json.loads(json_str)['data'])

    return dataframe







