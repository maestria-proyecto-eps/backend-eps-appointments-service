from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db_admin
from app.models.minimal_models import Usuario
from app.core.auth_utils import get_current_user_id

def get_usuario_actual(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_admin)
) -> Usuario:
    user = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.id_usuario == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado en el sistema"
        )

    return user


class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Usuario = Depends(get_usuario_actual)) -> Usuario:
        if (
            user.rol.nombre_rol not in self.allowed_roles
            and user.rol.nombre_rol != "Administrador"
        ):
            raise HTTPException(
                status_code=403,
                detail={
                    "hasError": True,
                    "Message": f"Acceso denegado. Se requiere uno de estos roles: {self.allowed_roles}",
                    "Data": None
                }
            )
        return user