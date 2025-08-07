#!/usr/bin/env python3
"""
Database setup script for Energy Conservation API
Supports both PostgreSQL and SQLite databases
"""

import asyncio
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg
import logging

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import Base, engine
from app.models import users, devices, energy_data  # Import all models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_postgresql_database():
    """Create PostgreSQL database if it doesn't exist"""
    try:
        # Parse the DATABASE_URL to get connection details
        from app.config import settings
        db_url = settings.DATABASE_URL
        
        if not db_url.startswith('postgresql'):
            logger.info("Not a PostgreSQL database, skipping PostgreSQL setup")
            return False
            
        # Extract database name and connection details
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        db_name = parsed.path[1:]  # Remove leading slash
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5432
        username = parsed.username
        password = parsed.password
        
        logger.info(f"Attempting to create PostgreSQL database: {db_name}")
        
        # Connect to PostgreSQL server (not to specific database)
        try:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database='postgres'  # Connect to default postgres database
            )
            
            # Check if database exists
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db_name
            )
            
            if not result:
                # Create database
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"Created PostgreSQL database: {db_name}")
            else:
                logger.info(f"PostgreSQL database {db_name} already exists")
                
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL database: {e}")
            logger.info("You may need to create the database manually or check your PostgreSQL setup")
            return False
            
    except Exception as e:
        logger.error(f"Error in PostgreSQL setup: {e}")
        return False


def create_sqlite_database():
    """Create SQLite database (simpler alternative)"""
    try:
        from app.config import settings
        
        # Check if we should use SQLite
        if 'sqlite' not in settings.DATABASE_URL.lower():
            return False
            
        logger.info("Setting up SQLite database...")
        
        # SQLite database will be created automatically when we create tables
        return True
        
    except Exception as e:
        logger.error(f"Error in SQLite setup: {e}")
        return False


async def create_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        
        async with engine.begin() as conn:
            # Drop all tables (for clean setup)
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Dropped existing tables")
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Created all tables successfully")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


async def insert_sample_data():
    """Insert sample data for testing"""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.database import AsyncSessionLocal
        from app.models.users import User
        from app.models.devices import Device, DeviceType
        from app.models.energy_data import EnergyData
        from datetime import datetime, timedelta
        
        logger.info("Inserting sample data...")
        
        async with AsyncSessionLocal() as session:
            # Create sample user
            sample_user = User(
                email="demo@energyapp.com",
                username="demo_user",
                full_name="Demo User",
                energy_goal_kwh=300.0,
                preferred_temperature=22.0
            )
            session.add(sample_user)
            await session.flush()  # Get the user ID
            
            # Create sample devices
            devices_data = [
                {
                    "name": "Living Room AC",
                    "device_type": DeviceType.HVAC,
                    "model": "EcoAir 2000",
                    "manufacturer": "EcoTech",
                    "location": "Living Room",
                    "rated_power_watts": 2000.0,
                    "is_smart_device": True
                },
                {
                    "name": "Kitchen Lights",
                    "device_type": DeviceType.LIGHTING,
                    "model": "LED Panel",
                    "manufacturer": "BrightLED",
                    "location": "Kitchen",
                    "rated_power_watts": 50.0,
                    "is_smart_device": True
                },
                {
                    "name": "Refrigerator",
                    "device_type": DeviceType.APPLIANCE,
                    "model": "CoolMax Pro",
                    "manufacturer": "CoolTech",
                    "location": "Kitchen",
                    "rated_power_watts": 150.0,
                    "is_smart_device": False
                }
            ]
            
            sample_devices = []
            for device_data in devices_data:
                device = Device(user_id=sample_user.id, **device_data)
                session.add(device)
                sample_devices.append(device)
            
            await session.flush()  # Get device IDs
            
            # Create sample energy data for the last 7 days
            base_time = datetime.utcnow() - timedelta(days=7)
            
            for device in sample_devices:
                for day in range(7):
                    for hour in range(0, 24, 6):  # Every 6 hours
                        timestamp = base_time + timedelta(days=day, hours=hour)
                        
                        # Simulate different consumption patterns
                        if device.device_type == DeviceType.HVAC:
                            consumption = 1.5 + (0.5 if 10 <= hour <= 18 else 0)  # More during day
                            power = 1800 + (200 if 10 <= hour <= 18 else -200)
                        elif device.device_type == DeviceType.LIGHTING:
                            consumption = 0.05 + (0.02 if hour >= 18 or hour <= 6 else 0)  # More at night
                            power = 45 + (10 if hour >= 18 or hour <= 6 else -10)
                        else:  # Appliance
                            consumption = 0.8 + (day * 0.1)  # Gradually increasing
                            power = 140 + (day * 5)
                        
                        energy_data = EnergyData(
                            user_id=sample_user.id,
                            device_id=device.id,
                            consumption_kwh=consumption,
                            power_watts=power,
                            cost_usd=consumption * 0.12,  # $0.12 per kWh
                            temperature_celsius=20.0 + (hour / 24 * 5),  # Simulate temp variation
                            timestamp=timestamp
                        )
                        session.add(energy_data)
            
            await session.commit()
            logger.info(f"Inserted sample data: 1 user, {len(sample_devices)} devices, and energy data")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert sample data: {e}")
        return False


async def main():
    """Main setup function"""
    logger.info("Starting database setup...")
    
    from app.config import settings
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Try to create database (PostgreSQL only)
    if 'postgresql' in settings.DATABASE_URL:
        await create_postgresql_database()
    elif 'sqlite' in settings.DATABASE_URL:
        create_sqlite_database()
    
    # Create tables
    tables_created = await create_tables()
    if not tables_created:
        logger.error("Failed to create tables. Exiting.")
        return False
    
    # Insert sample data
    sample_data_inserted = await insert_sample_data()
    if sample_data_inserted:
        logger.info("Database setup completed successfully!")
    else:
        logger.warning("Database setup completed but sample data insertion failed")
    
    logger.info("\n" + "="*50)
    logger.info("Database setup summary:")
    logger.info(f"- Database URL: {settings.DATABASE_URL}")
    logger.info(f"- Tables created: {'✓' if tables_created else '✗'}")
    logger.info(f"- Sample data: {'✓' if sample_data_inserted else '✗'}")
    logger.info("="*50)
    
    return True


if __name__ == "__main__":
    # Run the setup
    asyncio.run(main())