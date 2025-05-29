import json

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse

from utils.logger import get_logger
from analysis import read_ratings
from xlsx_to_json import validate_excel, prepare_json, test_firebase
from utils.data_management import RatingsParams
from utils.endpoint_utils import return_file_path

import pandas as pd

logger = get_logger(__name__)


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
        contents_of_xlsx: bytes = await xlsx_file.read()

        try:
            xlsx_ratings_sheet: pd.DataFrame = pd.read_excel(contents_of_xlsx,  # type: ignore
                                                             sheet_name=2,
                                                             header=2,
                                                             index_col=0,
                                                             usecols=[0] + list(range(19, 37)))

            validation_flag: bool = validate_excel(xlsx_ratings_sheet)

            if validation_flag is False:
                return JSONResponse(status_code=400, content={"error": "Invalid Excel format"})

            if validation_flag is True:
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

    @app.get("/display")
    async def display(year: str, month: str, day: str, startHour: str, endHour: str) -> JSONResponse:
        """Receives strings in the format: YYYY, MM, DD, HH, HH. Creates a back-end/storage request based
        on these strings using RatingsParams dataclass.

        >>>RatingsParams

        Example: "2025", "05", "17", "20", "23"
        """

        request_params = RatingsParams(year=year,
                                       month=month,
                                       day=day,
                                       start_hour=startHour,
                                       end_hour=endHour)

        try:
            ratings_data: str = read_ratings(file_path=return_file_path(request_params.file_path), time_range=request_params.time_range)

            try:
                json_content: dict = json.loads(ratings_data)
                return JSONResponse(
                    content=json_content,
                    status_code=200
                )
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error: {json_err}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Invalid JSON format: {str(json_err)}"}
                )
        except FileNotFoundError:
            logger.error(f"File not found: {request_params.file_path}")
            return JSONResponse(
                status_code=404,
                content={"error": "File not found"}
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing file: {str(e)}"}
            )

    @app.get("/test_firebase")
    async def test_firebase_connection():
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
