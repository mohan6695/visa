"""
Main FastAPI application for Visa Platform
Implements microservices architecture with proper scaling considerations
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from contextlib import asynccontextmanager

from src.api.v1.api import api_router
from src.core.config import get_settings
from src.core.database import engine
from src.core.cache import get_redis_client
from src.core.logging import setup_logging
from src.core.exceptions import (
    VisaPlatformException,
    ValidationException,
    NotFoundException,
    UnauthorizedException
)
from src.api.deps import get_current_user
from src.utils.health_check import setup_health_checks

# Setup logging
setup_logging()
logger = structlog.get_logger()

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Visa Platform API", version="1.0.0")
    
    # Initialize database
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda x: None)  # Test connection
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise
    
    # Initialize Redis
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))
        raise
    
    # Initialize search index
    try:
        from src.services.search import SearchService
        search_service = SearchService()
        await search_service.initialize()
        logger.info("Search service initialized")
    except Exception as e:
        logger.warning("Search service initialization failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Visa Platform API")


# Create FastAPI app
app = FastAPI(
    title="Visa Platform API",
    description="Scalable visa information and community platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Rate limiting middleware
from src.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(VisaPlatformException)
async def visa_platform_exception_handler(request: Request, exc: VisaPlatformException):
    logger.error(
        "Visa platform exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code}
    )

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.detail, "error_code": "VALIDATION_ERROR"}
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail, "error_code": "NOT_FOUND"}
    )

@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail, "error_code": "UNAUTHORIZED"}
    )

# API routes
app.include_router(api_router, prefix="/api/v1")

# Health checks
setup_health_checks(app)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Visa Platform API",
        "version": "1.0.0",
        "status": "operational"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )