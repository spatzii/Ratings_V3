from pathlib import Path
from datetime import datetime
import pandas as pd
import json


project_dir = Path("C:/Users/panas/PycharmProjects/ratings_backend")
my_file = project_dir / "Digi 24-audiente zilnice la minut 2025-05-02.xlsx"

parsed_file = pd.read_excel(my_file, sheet_name=2, header=2, index_col=0, usecols= [0] + list(range(18,37)))  # type: ignore

def validate_excel(file):

    if file.columns[5] != "Digi 24.1":
        print("Error")
        return "Error"

    else:
        return save_json(file)
def save_json(file):

    output_path = Path(f"ratings_data/{extract_date_from_filename(my_file)}.json")

    if output_path.exists(): # LOGIC HERE
        print(f"File {output_path} already exists, skipping...")
        return output_path


    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_data = file.to_json(orient='table')

    with open(output_path, 'w') as f:
        json.dump(json.loads(json_data), f, indent=2)

    return output_path

def extract_date_from_filename(filename):
    filename = str(filename).split(' ')[-1].replace('.xlsx', '')
    return filename


validate_excel(parsed_file)
