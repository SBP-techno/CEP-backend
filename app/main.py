from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.database import init_db
from app.routers import energy, ai_recommendations
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


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