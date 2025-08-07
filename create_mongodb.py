#!/usr/bin/env python3
"""
MongoDB setup script for Energy Conservation API
Creates database, collections, and inserts sample data
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import logging

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import connect_to_mongo, close_mongo_connection, init_db
from app.models.users import User
from app.models.devices import Device, DeviceType
from app.models.energy_data import EnergyData
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_mongodb_connection():
    """Check if MongoDB is running and accessible"""
    try:
        await connect_to_mongo()
        logger.info("✓ Successfully connected to MongoDB")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to connect to MongoDB: {e}")
        logger.error("Please ensure MongoDB is running and accessible at the configured URL")
        return False


async def create_sample_data():
    """Create sample data for testing the API"""
    try:
        logger.info("Creating sample data...")
        
        # Create sample user
        sample_user = User(
            email="demo@energyapp.com",
            username="demo_user",
            full_name="Demo User",
            energy_goal_kwh=300.0,
            preferred_temperature=22.0,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        await sample_user.insert()
        logger.info(f"Created user: {sample_user.username} ({sample_user.email})")
        
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
                "model": "LED Panel Pro",
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
            },
            {
                "name": "Water Heater",
                "device_type": DeviceType.WATER_HEATER,
                "model": "HeatMaster 3000",
                "manufacturer": "WarmTech",
                "location": "Basement",
                "rated_power_watts": 3000.0,
                "is_smart_device": True
            },
            {
                "name": "Solar Panel Array",
                "device_type": DeviceType.SOLAR_PANEL,
                "model": "SolarMax 5kW",
                "manufacturer": "SunPower",
                "location": "Roof",
                "rated_power_watts": 5000.0,
                "is_smart_device": True
            }
        ]
        
        sample_devices = []
        for device_data in devices_data:
            device = Device(
                user_id=sample_user.id,
                is_active=True,
                created_at=datetime.utcnow(),
                **device_data
            )
            await device.insert()
            sample_devices.append(device)
            logger.info(f"Created device: {device.name} ({device.device_type.value})")
        
        # Create sample energy data for the last 30 days
        logger.info("Generating energy data for the last 30 days...")
        base_time = datetime.utcnow() - timedelta(days=30)
        
        energy_records = []
        for device in sample_devices:
            for day in range(30):
                for hour in range(0, 24, 4):  # Every 4 hours = 6 readings per day
                    timestamp = base_time + timedelta(days=day, hours=hour)
                    
                    # Simulate different consumption patterns based on device type
                    if device.device_type == DeviceType.HVAC:
                        # AC usage higher during day and varies by season
                        base_consumption = 2.0
                        if 8 <= hour <= 20:  # Day time
                            consumption = base_consumption * 1.5
                            power = 2200
                        else:  # Night time
                            consumption = base_consumption * 0.7
                            power = 1400
                        production = 0.0
                        
                    elif device.device_type == DeviceType.LIGHTING:
                        # Lights used more in evening/night
                        if 18 <= hour <= 23 or 6 <= hour <= 8:
                            consumption = 0.08
                            power = 48
                        else:
                            consumption = 0.02
                            power = 12
                        production = 0.0
                        
                    elif device.device_type == DeviceType.APPLIANCE:
                        # Refrigerator - constant but varies slightly
                        consumption = 0.6 + (day * 0.01)  # Slight increase over time
                        power = 145 + (day * 2)
                        production = 0.0
                        
                    elif device.device_type == DeviceType.WATER_HEATER:
                        # Water heater - peaks in morning and evening
                        if 6 <= hour <= 8 or 18 <= hour <= 21:
                            consumption = 1.8
                            power = 2800
                        else:
                            consumption = 0.3
                            power = 450
                        production = 0.0
                        
                    elif device.device_type == DeviceType.SOLAR_PANEL:
                        # Solar panels - produce during day
                        consumption = 0.0
                        power = 0
                        if 7 <= hour <= 18:  # Daylight hours
                            # Peak production around noon
                            hour_factor = 1 - abs(12.5 - hour) / 6
                            production = 4.0 * hour_factor * (0.8 + day * 0.01)
                        else:
                            production = 0.0
                    
                    else:
                        consumption = 0.5
                        power = 100
                        production = 0.0
                    
                    # Add some randomness for realism
                    import random
                    consumption *= (0.8 + random.random() * 0.4)
                    if power > 0:
                        power *= (0.8 + random.random() * 0.4)
                    if production > 0:
                        production *= (0.8 + random.random() * 0.4)
                    
                    # Environmental data
                    temp = 20 + (hour / 24 * 8) + random.random() * 4  # Temp varies during day
                    humidity = 40 + random.random() * 20
                    
                    energy_record = EnergyData(
                        user_id=sample_user.id,
                        device_id=device.id,
                        consumption_kwh=round(consumption, 3),
                        production_kwh=round(production, 3),
                        power_watts=round(power, 1) if power > 0 else None,
                        voltage=120.0 + random.random() * 10,
                        current_amps=round(power / 120, 2) if power > 0 else None,
                        temperature_celsius=round(temp, 1),
                        humidity_percent=round(humidity, 1),
                        cost_usd=round(consumption * 0.12, 3),  # $0.12 per kWh
                        timestamp=timestamp,
                        created_at=datetime.utcnow()
                    )
                    
                    energy_records.append(energy_record)
        
        # Insert energy records in batches for better performance
        batch_size = 100
        total_records = len(energy_records)
        
        for i in range(0, total_records, batch_size):
            batch = energy_records[i:i + batch_size]
            await EnergyData.insert_many(batch)
            logger.info(f"Inserted energy records {i + 1}-{min(i + batch_size, total_records)} of {total_records}")
        
        logger.info(f"✓ Sample data creation completed!")
        logger.info(f"  - Created 1 user: {sample_user.username}")
        logger.info(f"  - Created {len(sample_devices)} devices")
        logger.info(f"  - Created {total_records} energy data records over 30 days")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create sample data: {e}")
        return False


async def clear_existing_data():
    """Clear existing data from collections"""
    try:
        logger.info("Clearing existing data...")
        
        # Clear collections
        await User.delete_all()
        await Device.delete_all()
        await EnergyData.delete_all()
        
        logger.info("✓ Cleared existing data")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to clear existing data: {e}")
        return False


async def main():
    """Main setup function"""
    logger.info("=" * 60)
    logger.info("MongoDB Energy Conservation API Setup")
    logger.info("=" * 60)
    
    logger.info(f"MongoDB URL: {settings.MONGODB_URL}")
    logger.info(f"Database Name: {settings.DATABASE_NAME}")
    
    # Check MongoDB connection
    if not await check_mongodb_connection():
        logger.error("Cannot proceed without MongoDB connection. Exiting.")
        return False
    
    try:
        # Initialize database and models
        await init_db()
        logger.info("✓ Database initialized successfully")
        
        # Ask user if they want to clear existing data
        if "--clear" in sys.argv or "--force" in sys.argv:
            clear_data = True
        else:
            clear_data = input("\nClear existing data? (y/N): ").lower().startswith('y')
        
        if clear_data:
            await clear_existing_data()
        
        # Create sample data
        if "--sample" in sys.argv or "--force" in sys.argv:
            create_sample = True
        else:
            create_sample = input("Create sample data? (Y/n): ").lower() != 'n'
        
        if create_sample:
            success = await create_sample_data()
            if not success:
                logger.error("Sample data creation failed")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ MongoDB setup completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Start the API server: uvicorn app.main:app --reload")
        logger.info("2. Visit the API docs: http://localhost:8000/docs")
        logger.info("3. Test the endpoints with the sample data")
        
        if create_sample:
            logger.info("\nSample user credentials:")
            logger.info("- Email: demo@energyapp.com")
            logger.info("- Username: demo_user")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Setup failed: {e}")
        return False
    
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    # Run the setup
    success = asyncio.run(main())
    sys.exit(0 if success else 1)