from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database status
db_connected = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with graceful database handling"""
    global db_connected
    
    # Startup
    try:
        from app.database import init_db, close_mongo_connection
        await init_db()
        db_connected = True
        logger.info("Database connected successfully")
    except Exception as e:
        db_connected = False
        logger.warning(f"Database connection failed: {e}")
        logger.warning("API will run in limited mode without database")
    
    yield
    
    # Shutdown
    try:
        from app.database import close_mongo_connection
        await close_mongo_connection()
        logger.info("Database connection closed")
    except Exception as e:
        logger.warning(f"Error closing database connection: {e}")

app = FastAPI(
    title="Energy Conservation API",
    description="API for energy conservation app with AI-powered recommendations using MongoDB",
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

# Include routers only if database is connected
if db_connected:
    try:
        from app.routers import energy, ai_recommendations
        app.include_router(energy.router, prefix="/api/v1/energy", tags=["energy"])
        app.include_router(ai_recommendations.router, prefix="/api/v1/ai", tags=["ai"])
        logger.info("API routers loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load API routers: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Energy Conservation API", 
        "version": "1.0.0",
        "database": "MongoDB",
        "database_status": "connected" if db_connected else "disconnected",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global db_connected
    
    try:
        if db_connected:
            from app.database import get_client
            client = get_client()
            if client:
                await client.admin.command('ping')
                db_status = True
            else:
                db_status = False
        else:
            db_status = False
    except Exception as e:
        db_status = False
        logger.warning(f"Database health check failed: {e}")
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "api_status": "running",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint that doesn't require database"""
    return {
        "message": "API is working",
        "database_required": False,
        "status": "success"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )