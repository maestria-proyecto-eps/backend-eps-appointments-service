from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from app.core.logger import setup_logging
from app.routers import appointments_router, health_router

app = FastAPI(
    title="EPS API 2",
    description="API de gestion EPS 2",
    version="0.1"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logging()

# Logger call example
#logger = get_logger(__name__)

app.include_router(health_router)
app.include_router(appointments_router)


async def _database_exception_response(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Error de conexion con la base de datos. Verifica credenciales y disponibilidad del servicio.",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return await _database_exception_response(request, exc)


@app.exception_handler(DBAPIError)
async def dbapi_exception_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    return await _database_exception_response(request, exc)
