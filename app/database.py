from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global database client
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Create database connection."""
    global client, database
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        database = client[settings.DATABASE_NAME]
        
        # Test the connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection."""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    """Create database indexes for better performance."""
    try:
        # Users collection indexes
        await database.users.create_index("email", unique=True)
        await database.users.create_index("username", unique=True)
        
        # Devices collection indexes
        await database.devices.create_index("user_id")
        await database.devices.create_index("device_type")
        await database.devices.create_index([("user_id", 1), ("device_type", 1)])
        
        # Energy data collection indexes
        await database.energy_data.create_index("device_id")
        await database.energy_data.create_index("user_id")
        await database.energy_data.create_index("timestamp")
        await database.energy_data.create_index([("device_id", 1), ("timestamp", -1)])
        await database.energy_data.create_index([("user_id", 1), ("timestamp", -1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")


async def init_db():
    """Initialize database connection."""
    await connect_to_mongo()


def get_database():
    """Get database instance."""
    return database


def get_client():
    """Get MongoDB client instance."""
    return client