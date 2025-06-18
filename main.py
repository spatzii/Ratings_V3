from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from utils.firebase_init import initialize_firebase
from contextlib import asynccontextmanager

from endpoints import setup_routes
from utils.config import current_config
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    initialize_firebase()
    yield
    # Shutdown code (if any)

app = FastAPI(lifespan=lifespan,
              openapi_url = "/openapi.json"
)

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

setup_routes(app)

print("Debug Information:")
print(f"ENV variable: {os.getenv('ENV')}")
print(f"Config class: {current_config.__class__.__name__}")
print(f"Storage type: {current_config.STORAGE_TYPE}")
print(f"Project root: {current_config.PROJECT_ROOT}")