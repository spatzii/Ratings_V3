
import os
import asyncio

from services.xlsx_parser import XlsxParser
from services.download_service import RatingsDownloader
from services.daily_report_generator import DailyReportGenerator
from services.email_service import fetch_ratings_credentials, send_report


from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from pathlib import Path
from api.v1.router import api_router

from utils.config import current_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    if os.getenv("RUN_TEST_ON_STARTUP") == "1":
        await test()
    yield
    # Shutdown code (if any)

app = FastAPI(lifespan=lifespan,
              openapi_url = "/openapi.json"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response


# Add CORS middleware to allow requests from your Firebase app
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(api_router, prefix="/api/v1")

print("Debug Information:")
print(f"ENV variable: {os.getenv('ENV')}")
print(f"Config class: {current_config.__class__.__name__}")
print(f"Project root: {current_config.PROJECT_ROOT}")

async def test():
    test_file = Path("//Data/Ratings/Digi 24-audiente zilnice la minut 2026-01-26.xlsx")
    with open(test_file, "rb") as f:
        parser = XlsxParser(f.read(), test_file.name)
        cleaned = await parser.process_ratings_file()
        print(cleaned["data"][:5])

async def main():
    link_and_pass = fetch_ratings_credentials()
    if link_and_pass is None:
        return

    password, link = link_and_pass

    file_downloader = RatingsDownloader()
    download = file_downloader.download(password, link)

    report_generator = DailyReportGenerator(Path(current_config.DOWNLOAD_DIR / download.name),
                                           include_slot_averages=True)
    report = await report_generator.generate_report()

    # For email body
    html_report = report_generator.to_html(report)

    send_report(html_report, "pana.stefan@gmail.com")
    send_report(html_report, "citre.cristian@gmail.com")


if __name__ == "__main__":
    asyncio.run(main())