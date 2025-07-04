# api/v1/endpoints/__init__.py
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from utils.reqest_management import RequestParams
from services.database_service import DatabaseService, RatingsTable
from services.ratings_file_service import RatingsFileService
from postgrest.exceptions import APIError
import pandas as pd

# Export routers
from .root import router as root_router
from .upload import router as upload_router
from .display import router as display_router

__all__ = ['root_router', 'upload_router', 'display_router']

