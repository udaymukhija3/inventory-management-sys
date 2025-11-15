from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
from prometheus_client import make_asgi_app
from app.config import get_settings
from app.api import predictions, analytics, health
from app.utils.database import init_mongodb, init_redis, close_connections
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import MetricsMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Analytics Service...")
    
    # Initialize database connections
    await init_mongodb()
    await init_redis()
    
    # Model manager removed (no ML components)
    
    logger.info("Analytics Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Analytics Service...")
    await close_connections()
    logger.info("Analytics Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Inventory Analytics Service",
    description="Inventory analytics and data aggregation service",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(
    predictions.router, 
    prefix=f"{settings.api_prefix}/analytics", 
    tags=["Analytics"]
)
app.include_router(
    analytics.router, 
    prefix=f"{settings.api_prefix}/analytics", 
    tags=["Analytics"]
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url)
        }
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Inventory Analytics Service",
        "version": settings.version,
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/api/docs",
            "analytics": f"{settings.api_prefix}/analytics"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )
