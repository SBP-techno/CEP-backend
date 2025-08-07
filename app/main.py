from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.database import connect_to_mongo, close_mongo_connection, init_db
from app.routers import energy_mongo as energy, ai_recommendations
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up Energy Conservation API...")
    try:
        await connect_to_mongo()
        await init_db()
        logger.info("Database connection established and initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Energy Conservation API...")
    await close_mongo_connection()


app = FastAPI(
    title="Energy Conservation API",
    description="API for energy conservation app with AI-powered recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(energy.router, prefix="/api/v1/energy", tags=["energy"])
app.include_router(ai_recommendations.router, prefix="/api/v1/ai", tags=["ai"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Energy Conservation API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )