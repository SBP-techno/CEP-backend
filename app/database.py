from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
mongodb_client: AsyncIOMotorClient = None
mongodb_database: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    """Create database connection"""
    global mongodb_client, mongodb_database
    
    try:
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb_database = mongodb_client[settings.DATABASE_NAME]
        
        # Test the connection
        await mongodb_client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    global mongodb_client
    
    if mongodb_client:
        mongodb_client.close()
        logger.info("Disconnected from MongoDB")


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return mongodb_database


async def init_db():
    """Initialize database with Beanie ODM"""
    try:
        # Import all document models
        from app.models.users import User
        from app.models.devices import Device
        from app.models.energy_data import EnergyData
        
        # Initialize Beanie with the models
        await init_beanie(
            database=mongodb_database,
            document_models=[User, Device, EnergyData]
        )
        
        logger.info("Initialized Beanie ODM with MongoDB")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        # Import models to access collections
        from app.models.users import User
        from app.models.devices import Device
        from app.models.energy_data import EnergyData
        
        # Create indexes on commonly queried fields
        
        # User indexes
        await User.get_motor_collection().create_index("email", unique=True)
        await User.get_motor_collection().create_index("username", unique=True)
        await User.get_motor_collection().create_index("is_active")
        
        # Device indexes
        await Device.get_motor_collection().create_index("user_id")
        await Device.get_motor_collection().create_index("device_type")
        await Device.get_motor_collection().create_index("is_active")
        await Device.get_motor_collection().create_index([("user_id", 1), ("is_active", 1)])
        
        # Energy data indexes
        await EnergyData.get_motor_collection().create_index("user_id")
        await EnergyData.get_motor_collection().create_index("device_id")
        await EnergyData.get_motor_collection().create_index("timestamp")
        await EnergyData.get_motor_collection().create_index([("user_id", 1), ("timestamp", -1)])
        await EnergyData.get_motor_collection().create_index([("device_id", 1), ("timestamp", -1)])
        
        logger.info("Created database indexes")
        
    except Exception as e:
        logger.warning(f"Failed to create some indexes: {e}")


# Dependency to get database
async def get_db():
    """Dependency to get database instance"""
    return mongodb_database