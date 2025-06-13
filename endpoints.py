
from fastapi import FastAPI, UploadFile, File, Request, Depends
from fastapi.responses import JSONResponse

from utils.logger import get_logger
from xlsx_to_json import test_firebase
from utils.data_management import RequestParams
from services.ratings_service import RatingsService


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
            ratings_service = RatingsService(contents_of_xlsx, xlsx_file.filename)

            processed_file:dict = await ratings_service.process_ratings()
            result_path = await ratings_service.upload_ratings(processed_file)

            # THIS NEEDS TO BE CUSTOMIZABLE
            time_range = ("20:00", "22:59")  # You might want to make this configurable
            channels = ["Digi 24", "Antena 3 CNN"]  # Get this from your configuration or request

            ratings_data = await ratings_service.get_ratings(result_path, time_range, channels)

            return JSONResponse(
                content={
                    "message": "File processed successfully",
                    "path": result_path,
                    "ratings": ratings_data
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
            ratings_data = await RatingsService.get_ratings(
                file_path=params.file_path,
                time_range=params.time_range,
                channels=params.channels
            )
            return JSONResponse(content=ratings_data)
        except FileNotFoundError:
            logger.error(f"File not found: {params.file_path}")
            return JSONResponse(status_code=404, content={"error": "File not found"})
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

    @app.get("/wake_render")
    async def wake_render():
        return JSONResponse(
            status_code=200,
            content="Render is running"
        )
