from fastapi import APIRouter
from .endpoints import root_router, upload_router, display_router

api_router = APIRouter()

api_router.include_router(root_router, tags=["root"])
api_router.include_router(upload_router, tags=["upload"])
api_router.include_router(display_router, tags=["display"])