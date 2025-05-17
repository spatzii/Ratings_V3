import json
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Header, Request
from fastapi.responses import JSONResponse

from config import config

from analysis import ratings_read_test
from utils import validate_excel, read_json

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
    async def upload_xlsx(file: UploadFile = File(...)):

        if not file.filename.endswith(".xlsx"):
            return JSONResponse(status_code=400, content={"error": "Invalid file type"})
        contents = await file.read()

        try:
            parsed_file = pd.read_excel(contents, sheet_name=2, header=2, index_col=0, usecols=[0] + list(range(19, 37)))  # type: ignore

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
        read_json(json_str)
        return JSONResponse(content={"message": "File processed successfully"})

    @app.get("/display")
    async def display(year: str, month: str, day: str):

        if current_config.STORAGE_TYPE == 'firebase':
            file_path = f"{current_config.STORAGE_PATH}/{year}/{month}/{year}-{month}-{day}.json"
        else:
            # For local storage, continue using Path
            file_path = Path(f"{current_config.STORAGE_PATH}/{year}/{month}/{year}-{month}-{day}.json")

        try:
            result = ratings_read_test(file_path)
            return JSONResponse(
                content=json.loads(result),
                status_code=200
            )
        except FileNotFoundError:
            return JSONResponse(
                status_code=404,
                content={"error": "File not found"}
            )
        except Exception as e:
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

