from .health import router as health_router
from .appointments import router as appointments_router

__all__ = ["health_router", "appointments_router"]
