from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import json
import io

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # print("1. Received file:", file.filename)  # Debug print

    if not file.filename.endswith(".xlsx"):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    contents = await file.read()
    # excel_data = io.BytesIO(contents)

    try:
        parsed_file = pd.read_excel(contents, sheet_name=2, header=2, index_col=0, usecols= [0] + list(range(18,37)))  # type: ignore

        validation_result = validate_excel(parsed_file, file.filename)

        if validation_result == "Error":
            return JSONResponse(status_code=400, content={"error": "Invalid Excel format"})

        return JSONResponse(content={"message": "File processed successfully", "result": str(validation_result)})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Error processing file: {str(e)}"}
)

def validate_excel(file, original_filename):

    if file.columns[5] != "Digi 24.1":
        print("Error")
        return "Error"

    else:
        return save_json(file, original_filename)

def save_json(file, original_filename):

    output_path = Path(f"ratings_data/{extract_date_from_filename(original_filename)}.json")

    if output_path.exists(): # LOGIC HERE
        print(f"File {output_path} already exists, skipping...")
        return output_path
#
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_data = file.to_json(orient='table')

    with open(output_path, 'w') as f:
        json.dump(json.loads(json_data), f, indent=2)

    return output_path

def extract_date_from_filename(filename):
    filename = str(filename).split(' ')[-1].replace('.xlsx', '')
    return filename
