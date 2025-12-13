from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import engine
from . import models
from .routes import auth, fuzzy, licenses, files, api_config, admin_plans


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    settings.create_directories()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(fuzzy.router, prefix="/api", tags=["Fuzzy Matching"])
    app.include_router(licenses.router, prefix="/license", tags=["License Management"])
    app.include_router(files.router, prefix="/files", tags=["File Management"])
    app.include_router(api_config.router, prefix="/api/configurations", tags=["API Configuration"])
    app.include_router(admin_plans.router, tags=["Plan Administration"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app
