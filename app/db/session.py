from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# --- CONFIGURACION BASE DE DATOS ADMINISTRATIVA ---
# El motor administrativo se encarga de la gestion de medicos, usuarios y especialidades.
engine_admin = create_engine(
    settings.DB_ADMIN_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocalAdmin = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_admin,
)

BaseAdmin = declarative_base()

# --- CONFIGURACION BASE DE DATOS OPERATIVA ---
# El motor operativo gestiona las agendas, horarios y transacciones de citas.
engine_operativa = create_engine(
    settings.DB_OPERATIVA_URL,
    pool_pre_ping=True,
    pool_size=15, # Se asigna un pool mayor por la alta concurrencia de transacciones.
    max_overflow=25,
)

SessionLocalOperativa = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_operativa,
)

BaseOperativa = declarative_base()

# --- DEPENDENCIAS PARA FASTAPI ---

def get_db_admin() -> Generator:
    """
    Provee una sesion de base de datos para el esquema administrativo.
    Garantiza el cierre de la conexion tras finalizar la solicitud.
    """
    db = SessionLocalAdmin()
    try:
        yield db
    finally:
        db.close()

def get_db_operativa() -> Generator:
    """
    Provee una sesion de base de datos para el esquema operativo.
    Garantiza el cierre de la conexion tras finalizar la solicitud.
    """
    db = SessionLocalOperativa()
    try:
        yield db
    finally:
        db.close()

def get_db() -> Generator:
    """
    Mantiene compatibilidad con el codigo preexistente apuntando
    por defecto a la base de datos operativa.
    """
    db = SessionLocalOperativa()
    try:
        yield db
    finally:
        db.close()