from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import io

import read_json

app = FastAPI()

# Add CORS middleware to allow requests from your Firebase app
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace this with your Firebase app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")

async def root():
    return {
        "status": "success",
        "message": "Server is running correctly NEW"
    }


@app.post("/upload/xlsx")
async def upload_xlsx(file: UploadFile = File(...)):

    if not file.filename.endswith(".xlsx"):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    contents = await file.read()

    try:
        parsed_file = pd.read_excel(contents, sheet_name=2, header=2, index_col=0, usecols= [0] + list(range(19,37)))  # type: ignore

        validation_result = validate_excel(parsed_file, file.filename)

        if validation_result == "Error":
            return JSONResponse(status_code=400, content={"error": "Invalid Excel format"})

        return JSONResponse(content={"message": "File processed successfully", "result": str(validation_result)})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Error processing file: {str(e)}"})

@app.post("/upload/json")
async def upload_json(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    contents = await file.read()
    json_str = contents.decode('utf-8')
    read_json.read_json(json_str)
    return JSONResponse(content={"message": "File processed successfully"})


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