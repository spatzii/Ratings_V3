from datetime import datetime
from pathlib import Path

import pandas as pd

import json


def validate_excel(file, original_filename):

    if file.columns[4] != "Digi 24.1":
        print("Error")
        return "Error"

    else:
        return save_json(file, original_filename)
def save_json(file, original_filename):

    year, month = extract_year_and_month(original_filename)
    output_path = Path(f"ratings_data/{year}/{month}/{extract_date_from_filename(original_filename)}.json")

    if output_path.exists(): # LOGIC HERE
        print(f"File {output_path} already exists, skipping...")
        return output_path
#
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_data = file.to_json(orient='table')

    with open(output_path, 'w') as f:
        json.dump(json.loads(json_data), f, indent=2)

    return output_path

def extract_year_and_month(filename):
    filename = str(filename).split(' ')[-1].replace('.xlsx', '')
    date_obj= datetime.strptime(filename, '%Y-%m-%d')
    return str(date_obj.year), f"{date_obj.month:02d}"

def extract_date_from_filename(filename):
    filename = str(filename).split(' ')[-1].replace('.xlsx', '')
    return filename

def read_json(json_str):
    dataframe = pd.DataFrame(json.loads(json_str)['data'])

    return dataframe