from . import (
    APIRouter,
    Depends,
    JSONResponse,
    RequestParams,
    RatingsTable,
    pd,
)
from utils.logger import get_logger
logger = get_logger(__name__)  #

router = APIRouter()

@router.get("/display")

async def display(params: RequestParams = Depends(RequestParams.from_query)) -> JSONResponse:
    """Receives strings in the format: YYYY, MM, DD, HH, HH. Creates a back-end/storage request based
    on these strings using RatingsParams dataclass.

    >>>RequestParams

    Example: "2025", "05", "17", "20", "23"
    """

    try:

        ratings_data: pd.DataFrame = (RatingsTable.from_timeframe(date=params.request_date,
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
