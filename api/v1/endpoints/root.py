# api/v1/endpoints/root.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {
        "status": "success",
        "message": "Server is running correctly NEW"
    }