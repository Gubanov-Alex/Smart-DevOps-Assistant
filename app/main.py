"""FastAPI application factory and main entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import BaseAppException
from app.core.logging import setup_logging
import os


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    settings = get_settings()
    logger = structlog.get_logger()

    # Startup
    logger.info("Starting Smart DevOps Assistant", environment=settings.environment)

    # TODO: Initialize database connections, ML models, etc.
    # await initialize_database()
    # await load_ml_models()

    yield

    # Shutdown
    logger.info("Shutting down Smart DevOps Assistant")
    # TODO: Cleanup resources
    # await cleanup_database()
    # await cleanup_ml_models()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    # Setup logging
    setup_logging(
        level=settings.log_level,
        format_type=settings.log_format,
        development=settings.is_development,
    )

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        debug=settings.debug,
        lifespan=lifespan,
        openapi_url="/api/v1/openapi.json" if not settings.is_production else None,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # Security middleware
    if settings.is_production:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.yourdomain.com", "localhost"])

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.environment,
            "version": settings.api_version,
        }

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        """Root endpoint redirect to docs."""
        return {"message": "Smart DevOps Assistant API", "docs": "/docs"}

    # TODO: Include routers
    # app.include_router(api_router, prefix="/api/v1")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
