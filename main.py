from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from api.v1.router import api_router

from utils.config import current_config
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
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
print(f"Storage type: {current_config.STORAGE_TYPE}")
print(f"Project root: {current_config.PROJECT_ROOT}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
