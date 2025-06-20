
from fastapi import FastAPI, UploadFile, File, Request, Depends
from fastapi.responses import JSONResponse

from utils.logger import get_logger
from utils.firebase_init import test_firebase

from postgrest.exceptions import APIError

from services.database_service import DatabaseService, RatingsTable

from utils.reqest_management import RequestParams
from services.ratings_service import RatingsService

import pandas as pd

logger = get_logger(__name__)
# THIS NEEDS TO BE CUSTOMIZABLE
TIME_RANGE = ["20:00", "23:00"]  # You might want to make this configurable
CHANNELS = ["Digi 24", "Antena 3 CNN"] # Get this from your configuration or request

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
            ratings_service = RatingsService(contents_of_xlsx, xlsx_file.filename)
            processed_file:dict = await ratings_service.process_ratings()
            database_service = DatabaseService(processed_file)

            try:
                database_service.insert_tv_ratings()
            except APIError as e:
                if 'tv_ratings_Timebands_key' in str(e):
                    return JSONResponse(
                        status_code=409,
                        content={"message": "File already uploaded"}
                    )
                raise

            query = (RatingsTable.from_timeframe(date=ratings_service.date,
                                                timeframe = TIME_RANGE,
                                                channels = CHANNELS).
                     basetable())

            styled_html = query.to_html()

            return JSONResponse(
                content={'table': styled_html,
                         'metadata': {
                             'date': ratings_service.date
                         }
                         }

            )

        except ValueError as ve:
            return JSONResponse(status_code=400, content={"error": str(ve)})
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Error processing file: {str(e)}"})

    @app.get("/display")
    async def display(params: RequestParams = Depends(RequestParams.from_query)) -> JSONResponse:
        """Receives strings in the format: YYYY, MM, DD, HH, HH. Creates a back-end/storage request based
        on these strings using RatingsParams dataclass.

        >>>RequestParams

        Example: "2025", "05", "17", "20", "23"
        """

        try:

            ratings_data:pd.DataFrame = (RatingsTable.from_timeframe(date=params.request_date,
                                                       timeframe=params.time_range,
                                                       channels=params.channels
                                                       )
                            .basetable())

            styled_html = ratings_data.to_html()

            response_data = {
                'table': styled_html,
                'metadata': {
                    'date': params.request_date
                }
            }
            return JSONResponse(content=response_data)
        except FileNotFoundError:
            logger.error(f"Request date not found: {params.request_date}")
            return JSONResponse(status_code=404, content={"error": "Date not in database"})
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing request: {str(e)}"}
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

    @app.get("/wake_render")
    async def wake_render():
        return JSONResponse(
            status_code=200,
            content="Render is running"
        )
