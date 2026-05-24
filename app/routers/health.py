from fastapi import APIRouter

from app.services import get_health_status, get_root_payload

router = APIRouter()


@router.get("/")
def root() -> dict:
    """Root endpoint"""
    return get_root_payload()


@router.get("/health")
def health() -> dict:
    """Health endpoint"""
    return get_health_status()
