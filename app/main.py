from fastapi import FastAPI
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
