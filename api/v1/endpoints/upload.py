from . import (
    APIRouter,
    UploadFile,
    File,
    JSONResponse,
    RatingsFileService,
    DatabaseService,
    RatingsTable,
)
from core.config import Settings

router = APIRouter()

@router.post("/upload/xlsx")
async def upload_xlsx(xlsx_file: UploadFile = File(...)):
    if not xlsx_file.filename.endswith(".xlsx"):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})

    contents_of_xlsx: bytes = await xlsx_file.read()

    try:
        ratings_service = RatingsFileService(contents_of_xlsx, xlsx_file.filename)
        processed_file: dict = await ratings_service.process_ratings_file()
        melted_file: list[dict] = ratings_service.pivot_datatable(processed_file)
        database_service = DatabaseService(melted_file)

        database_service.insert_tv_ratings()
        ### TODO: Refactor this, but with SQLite instead of Postgres/APIError
        # try:
        #     database_service.insert_tv_ratings()
        # except APIError as e:
        #     if 'ratings_Timebands_key' in str(e):
        #         return JSONResponse(
        #             status_code=409,
        #             content={"message": "File already uploaded"}
        #         )
        #     raise

        query = (RatingsTable.from_timeframe(date=ratings_service.date,
                                             timeframe=Settings.TIME_RANGE,
                                             channels=Settings.CHANNELS).
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
