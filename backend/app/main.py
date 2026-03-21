from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import generic_exception_handler
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()

    application = FastAPI(
        title="Restaurant Chops",
        description="Restaurant Operations Backend",
        version=settings.APP_VERSION,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_exception_handler(Exception, generic_exception_handler)
    application.include_router(api_router)

    return application


app = create_app()
