def get_root_payload() -> dict:
    return {
        "message": "API EPS",
        "features": ["API de gestion EPS"],
        "docs": "/docs",
        "redoc": "/redoc",
    }


def get_health_status() -> dict:
    return {"message": "servicio activo"}
