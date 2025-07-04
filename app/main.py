"""FastAPI application factory and main entry point."""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import BaseAppException
from app.core.logging import setup_logging
from app.database.session import init_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    settings = get_settings()
    logger = structlog.get_logger()

    # Startup
    logger.info(
        "Starting Smart DevOps Assistant",
        environment=settings.environment,
        version=settings.api_version,
        debug=settings.debug,
    )

    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

    # TODO: Initialize other services
    # await init_redis()
    # await load_ml_models()
    # await start_background_tasks()

    logger.info("Application startup completed")

    yield

    # Shutdown
    logger.info("Shutting down Smart DevOps Assistant")
    # TODO: Cleanup resources
    # await cleanup_database()
    # await cleanup_redis()
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

    # Create FastAPI app with comprehensive configuration
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        debug=settings.debug,
        lifespan=lifespan,
        # API documentation configuration
        openapi_url="/api/v1/openapi.json" if not settings.is_production else None,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        # Additional OpenAPI metadata
        openapi_tags=[
            {
                "name": "Health Check",
                "description": "System health monitoring and status endpoints",
            },
            {
                "name": "API Info",
                "description": "API metadata and information endpoints",
            },
            {
                "name": "Log Management",
                "description": "Log ingestion, analysis, and retrieval operations",
            },
            {
                "name": "Incident Management",
                "description": "Incident detection, tracking, and resolution workflows",
            },
            {
                "name": "ML Models",
                "description": "Machine learning model management and predictions",
            },
            {
                "name": "Analytics",
                "description": "Data analytics and reporting endpoints",
            },
        ],
        contact={
            "name": "Smart DevOps Support",
            "email": "support@smartdevops.ai",
            "url": "https://support.smartdevops.ai",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=(
            [
                {
                    "url": "https://api.smartdevops.ai",
                    "description": "Production server",
                },
                {
                    "url": "https://staging-api.smartdevops.ai",
                    "description": "Staging server",
                },
                {
                    "url": "http://localhost:8000",
                    "description": "Development server",
                },
            ]
            if not settings.is_development
            else [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server",
                }
            ]
        ),
    )

    # Security middleware
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[
                "*.smartdevops.ai",
                "*.yourdomain.com",
                "localhost",
                "127.0.0.1",
            ],
        )

    # CORS middleware with environment-specific configuration
    allowed_origins = []
    if settings.is_development:
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
        ]
    elif settings.environment == "staging":
        allowed_origins = [
            "https://staging-app.smartdevops.ai",
            "https://staging.smartdevops.ai",
        ]
    elif settings.is_production:
        allowed_origins = [
            "https://app.smartdevops.ai",
            "https://smartdevops.ai",
            "https://www.smartdevops.ai",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID",
            "User-Agent",
            "Accept",
            "Accept-Language",
            "Cache-Control",
        ],
        expose_headers=[
            "X-Request-ID",
            "X-Rate-Limit-Remaining",
            "X-Rate-Limit-Reset",
        ],
        max_age=86400,  # 24 hours
    )

    # Request/Response middleware for logging and monitoring
    @app.middleware("http")
    async def request_middleware(request: Request, call_next) -> Response:
        """Middleware for request/response logging and monitoring."""
        start_time = time.time()

        # Generate request ID if not provided
        request_id = request.headers.get("X-Request-ID", "")
        if not request_id:
            import uuid

            request_id = str(uuid.uuid4())

        # Add request context to structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        logger = structlog.get_logger()

        # Log request
        logger.info(
            "Request started",
            user_agent=request.headers.get("User-Agent", ""),
            content_length=request.headers.get("Content-Length", 0),
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # Log response
            logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
            )

            return response

        except Exception as e:
            # Calculate processing time for error cases
            process_time = time.time() - start_time

            # Log error
            logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                process_time_ms=round(process_time * 1000, 2),
            )

            # Create error response
            error_response = JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )

            return error_response

    # Global exception handlers
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(
        request: Request, exc: BaseAppException
    ) -> JSONResponse:
        """Handle application-specific exceptions."""
        logger = structlog.get_logger()

        logger.error(
            "Application exception",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError exceptions."""
        logger = structlog.get_logger()
        logger.error("Value error", error=str(exc))

        return JSONResponse(
            status_code=400,
            content={
                "error": "INVALID_INPUT",
                "message": str(exc),
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc) -> JSONResponse:
        """Handle 404 Not Found errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "NOT_FOUND",
                "message": f"Endpoint {request.url.path} not found",
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

    # Include API routers
    app.include_router(api_router)

    # Root endpoint
    @app.get(
        "/",
        summary="API Root",
        description="Welcome endpoint with basic API information",
        tags=["API Info"],
    )
    async def root() -> dict:
        """API root endpoint with welcome message and basic information."""
        return {
            "message": "Welcome to Smart DevOps Assistant API",
            "version": settings.api_version,
            "status": "operational",
            "documentation": "/docs",
            "health_check": "/api/v1/health",
            "timestamp": time.time(),
        }

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
