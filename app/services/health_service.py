def get_root_payload() -> dict:
    return {
        "message": "EPS API",
        "features": ["EPS management API"],
        "docs": "/docs",
        "redoc": "/redoc",
    }


def get_health_status() -> dict:
    return {"message": "ok"}
