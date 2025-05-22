import json
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Header, Request
from fastapi.responses import JSONResponse

from config import config

from analysis import ratings_read_test
from utils import validate_original_excel_file, unpack_json_to_dataframe, prepare_json

import pandas as pd

# Get config based on environment
env = os.getenv('ENV', 'development')
current_config = config[env]


def setup_routes(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        print(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        return response

    @app.get("/")
    async def root():
        return {
            "status": "success",
            "message": "Server is running correctly NEW"
        }

    @app.post("/upload/xlsx")
    async def upload_xlsx(xlsx_file: UploadFile = File(...)):

        if not xlsx_file.filename.endswith(".xlsx"):
            return JSONResponse(status_code=400, content={"error": "Invalid file type"})
        contents_of_xlsx = await xlsx_file.read()

        try:
            xlsx_ratings_sheet = pd.read_excel(contents_of_xlsx,  # type: ignore
                                               sheet_name=2,
                                               header=2,
                                               index_col=0,
                                               usecols=[0] + list(range(19, 37)))

            validation_flag = validate_original_excel_file(xlsx_ratings_sheet)

            if validation_flag == "Error":
                return JSONResponse(status_code=400, content={"error": "Invalid Excel format"})

            if validation_flag is True:  # explicitly check for True
                try:
                    result_path = prepare_json(xlsx_ratings_sheet, xlsx_file.filename)
                    return JSONResponse(
                        content={
                            "message": "File processed successfully",
                            "path": result_path
                        }
                    )
                except Exception as prep_error:
                    return JSONResponse(
                        status_code=500,
                        content={"error": f"Error preparing JSON: {str(prep_error)}"}
                    )

            return JSONResponse(status_code=400, content={"error": "Validation failed"})

        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"Error processing file: {str(e)}"})

    @app.post("/upload/json")
    async def upload_json(file: UploadFile = File(...)):
        if not file.filename.endswith(".json"):
            return JSONResponse(status_code=400, content={"error": "Invalid file type"})
        contents = await file.read()
        json_str = contents.decode('utf-8')
        unpack_json_to_dataframe(json_str)
        return JSONResponse(content={"message": "File processed successfully"})

    @app.get("/display")
    async def display(year: str, month: str, day: str):
        try:
            if current_config.STORAGE_TYPE == 'firebase':
                file_path = f"{current_config.STORAGE_PATH}/{year}/{month}/{year}-{month}-{day}.json"
                print(f"Firebase path: {file_path}")
            else:
                file_path = Path(f"{current_config.STORAGE_PATH}/{year}/{month}/{year}-{month}-{day}.json")
                print(f"Local path: {file_path}")

            result = ratings_read_test(file_path)
            try:
                json_content = json.loads(result)
                return JSONResponse(
                    content=json_content,
                    status_code=200
                )
            except json.JSONDecodeError as json_err:
                print(f"JSON parsing error: {json_err}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Invalid JSON format: {str(json_err)}"}
                )
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return JSONResponse(
                status_code=404,
                content={"error": "File not found"}
            )
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing file: {str(e)}"}
            )

    @app.get("/test_firebase")
    async def test_firebase_connection():
        from utils import test_firebase
        result = test_firebase()
        if result["status"] == "error":
            return JSONResponse(
                status_code=400,
                content=result
            )
        return JSONResponse(
            content=result,
            status_code=200
        )

