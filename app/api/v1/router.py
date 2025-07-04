"""Main API router for version 1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

# Create main API router for version 1
api_router = APIRouter(
    prefix="/api/v1",
    responses={
        400: {"description": "Bad Request - Invalid input parameters"},
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request format"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error - Unexpected server error"},
        503: {"description": "Service Unavailable - Service temporarily unavailable"},
    },
)

# Include health check endpoints
api_router.include_router(health.router, tags=["Health Check"])


# TODO: Add more endpoint routers as they are implemented
# api_router.include_router(
#     logs.router,
#     tags=["Log Management"]
# )
#
# api_router.include_router(
#     incidents.router,
#     tags=["Incident Management"]
# )
#
# api_router.include_router(
#     ml_models.router,
#     tags=["ML Models"]
# )
#
# api_router.include_router(
#     analytics.router,
#     tags=["Analytics"]
# )


# Root API information endpoint
@api_router.get(
    "",
    summary="API Information",
    description="Get information about the Smart DevOps Assistant API",
    response_description="API metadata and available endpoints",
    tags=["API Info"],
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Smart DevOps Assistant API",
                        "version": "1.0.0",
                        "description": "AI-powered DevOps automation and monitoring platform",
                        "status": "operational",
                        "features": [
                            "Log analysis and classification",
                            "Incident detection and management",
                            "Performance monitoring",
                            "ML-powered anomaly detection",
                        ],
                        "endpoints": {
                            "health": "/api/v1/health",
                            "docs": "/docs",
                            "redoc": "/redoc",
                            "openapi": "/api/v1/openapi.json",
                        },
                        "links": {
                            "documentation": "https://docs.smartdevops.ai",
                            "support": "https://support.smartdevops.ai",
                            "status": "https://status.smartdevops.ai",
                        },
                    }
                }
            },
        }
    },
)
async def api_info() -> dict:
    """
    Get API information and available endpoints.

    Returns metadata about the Smart DevOps Assistant API including
    version information, available features, and useful links.
    """
    return {
        "name": "Smart DevOps Assistant API",
        "version": "1.0.0",
        "description": "AI-powered DevOps automation and monitoring platform",
        "status": "operational",
        "features": [
            "Intelligent log analysis and classification",
            "Automated incident detection and management",
            "Real-time performance monitoring and alerting",
            "ML-powered anomaly detection and prediction",
            "Infrastructure optimization recommendations",
            "Automated remediation workflows",
        ],
        "capabilities": {
            "log_processing": {
                "formats": ["JSON", "Plain text", "Syslog", "Custom"],
                "sources": ["Applications", "Infrastructure", "Security", "Network"],
                "features": ["Classification", "Anomaly detection", "Pattern matching"],
            },
            "incident_management": {
                "detection": "Automated",
                "classification": "ML-powered",
                "escalation": "Rule-based",
                "resolution": "Workflow-driven",
            },
            "monitoring": {
                "metrics": ["System", "Application", "Business"],
                "alerts": ["Threshold", "Anomaly", "Predictive"],
                "dashboards": "Customizable",
            },
        },
        "endpoints": {
            "health": "/api/v1/health",
            "health_simple": "/api/v1/health/simple",
            "liveness": "/api/v1/health/live",
            "readiness": "/api/v1/health/ready",
            "api_docs": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/api/v1/openapi.json",
        },
        "authentication": {
            "methods": ["API Key", "OAuth 2.0", "JWT"],
            "rate_limiting": "Yes",
            "scopes": ["read", "write", "admin"],
        },
        "data_formats": {
            "input": ["JSON", "XML", "CSV", "Plain text"],
            "output": ["JSON"],
            "encoding": "UTF-8",
        },
        "limits": {
            "request_size_mb": 10,
            "requests_per_minute": 1000,
            "concurrent_connections": 100,
        },
        "links": {
            "documentation": "https://docs.smartdevops.ai/api/v1",
            "support": "https://support.smartdevops.ai",
            "status_page": "https://status.smartdevops.ai",
            "github": "https://github.com/smartdevops/assistant",
            "community": "https://community.smartdevops.ai",
        },
        "contact": {
            "support_email": "support@smartdevops.ai",
            "technical_email": "tech@smartdevops.ai",
            "security_email": "security@smartdevops.ai",
        },
    }
