from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import settings
from app.core.database import async_session_factory, init_db
from app.core.logging import logger, setup_logging
from app.services.standard_service import StandardService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize logging, tables and seed verified standards
    setup_logging()
    logger.info("Initializing database schema...")
    await init_db()

    logger.info("Seeding verified Indian Standards into knowledge base...")
    async with async_session_factory() as session:
        standard_service = StandardService(session)
        await standard_service.seed_default_standards()
        await session.commit()

    logger.info(f"{settings.PROJECT_NAME} backend initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down backend services...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Pre-Certification Operating System for Indian Standards & BIS Services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception during {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

# Mount all API routes under /api
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs",
        "api_root": settings.API_V1_STR,
    }
