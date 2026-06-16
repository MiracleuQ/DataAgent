from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from app.config import get_settings, validate_settings
from app.api.routes import router as api_router
from app.api.websocket import router as ws_router
from app.utils.logger import setup_logger
from app.utils.metrics import get_metrics

logger = setup_logger(__name__)


def create_app() -> FastAPI:
    validate_settings()

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Natural Language Driven Multi-Agent Data Analysis System",
        version="1.0.0",
    )

    allow_origins = ["*"] if settings.app_env != "production" else []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(ws_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "env": settings.app_env}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics_prometheus():
        return get_metrics().export_prometheus()

    @app.get("/metrics/json")
    def metrics_json():
        return JSONResponse(content=get_metrics().export_json())

    logger.info("Application started: %s (env=%s)", settings.app_name, settings.app_env)
    return app


app = create_app()
