from fastapi import FastAPI, UploadFile, File, Header, Request
from fastapi.middleware.cors import CORSMiddleware

from endpoints import setup_routes
app = FastAPI()

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

