from typing import Generator
from sqlalchemy import create_engine, text, NullPool
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.auth_utils import get_current_user_id
from fastapi import Depends

# --- CONFIGURACION BASE DE DATOS ADMINISTRATIVA ---
# El motor administrativo se encarga de la gestion de medicos, usuarios y especialidades.
engine_admin = create_engine(
    settings.DB_ADMIN_URL,
    poolclass=NullPool
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
    poolclass=NullPool
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
        db.commit()       
    except Exception:
        db.rollback() 
        raise
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
        db.commit()       
    except Exception:
        db.rollback() 
        raise
    finally:
        db.close()
        
        
def get_db_admin_audit(
    user_id: int = Depends(get_current_user_id)
):
    db = SessionLocalAdmin()

    try:
        db.execute(
            text("SET LOCAL my.app_user_id = :uid"),
            {"uid": str(user_id)}
        )
        yield db
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        
def get_db_operativa_audit(
    user_id: int = Depends(get_current_user_id)
):
    db = SessionLocalOperativa()

    try:
        db.execute(
            text("SET LOCAL my.app_user_id = :uid"),
            {"uid": str(user_id)}
        )
        yield db
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()