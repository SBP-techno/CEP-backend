from fastapi import APIRouter, HTTPException, Query
from beanie import PydanticObjectId
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.users import User
from app.models.devices import Device
from app.models.energy_data import EnergyData
from app.schemas.energy import (
    User as UserSchema, UserCreate, UserUpdate, UserWithDevices,
    Device as DeviceSchema, DeviceCreate, DeviceUpdate, DeviceWithEnergyData,
    EnergyData as EnergyDataSchema, EnergyDataCreate, EnergyDataUpdate,
    EnergyStats, DailyEnergyStats
)

router = APIRouter()


# User endpoints
@router.post("/users/", response_model=UserSchema)
async def create_user(user: UserCreate):
    """Create a new user"""
    existing_user = await User.find_one(
        {"$or": [{"email": user.email}, {"username": user.username}]}
    )
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    
    db_user = User(**user.model_dump())
    await db_user.insert()
    return db_user


@router.get("/users/", response_model=List[UserSchema])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all users with pagination"""
    users = await User.find({"is_active": True}).skip(skip).limit(limit).to_list()
    return users


@router.get("/users/{user_id}", response_model=UserWithDevices)
async def get_user(user_id: PydanticObjectId):
    """Get a user by ID with their devices"""
    user = await User.get(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    devices = await Device.find({"user_id": user_id, "is_active": True}).to_list()
    
    user_dict = user.model_dump()
    user_dict["devices"] = devices
    
    return UserWithDevices(**user_dict)


@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(user_id: PydanticObjectId, user_update: UserUpdate):
    """Update a user"""
    user = await User.get(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await user.update({"$set": update_data})
    
    return await User.get(user_id)


@router.delete("/users/{user_id}")
async def delete_user(user_id: PydanticObjectId):
    """Soft delete a user"""
    user = await User.get(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    await user.update({"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
    return {"message": "User deleted successfully"}


# Device endpoints
@router.post("/users/{user_id}/devices/", response_model=DeviceSchema)
async def create_device(user_id: PydanticObjectId, device: DeviceCreate):
    """Create a new device for a user"""
    user = await User.get(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    device_data = device.model_dump()
    device_data["user_id"] = user_id
    
    db_device = Device(**device_data)
    await db_device.insert()
    return db_device


@router.get("/users/{user_id}/devices/", response_model=List[DeviceSchema])
async def get_user_devices(
    user_id: PydanticObjectId,
    include_inactive: bool = Query(False)
):
    """Get all devices for a user"""
    query = {"user_id": user_id}
    if not include_inactive:
        query["is_active"] = True
    
    devices = await Device.find(query).to_list()
    return devices


@router.get("/devices/{device_id}", response_model=DeviceWithEnergyData)
async def get_device(
    device_id: PydanticObjectId,
    include_recent_data: bool = Query(True),
    data_hours: int = Query(24, ge=1, le=168)
):
    """Get a device by ID with optional recent energy data"""
    device = await Device.get(device_id)
    
    if not device or not device.is_active:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device_dict = device.model_dump()
    
    if include_recent_data:
        since = datetime.utcnow() - timedelta(hours=data_hours)
        recent_data = await EnergyData.find(
            {
                "device_id": device_id,
                "timestamp": {"$gte": since}
            }
        ).sort([("timestamp", -1)]).limit(100).to_list()
        
        device_dict["recent_energy_data"] = recent_data
    
    return DeviceWithEnergyData(**device_dict)


@router.put("/devices/{device_id}", response_model=DeviceSchema)
async def update_device(device_id: PydanticObjectId, device_update: DeviceUpdate):
    """Update a device"""
    device = await Device.get(device_id)
    
    if not device or not device.is_active:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await device.update({"$set": update_data})
    
    return await Device.get(device_id)


@router.delete("/devices/{device_id}")
async def delete_device(device_id: PydanticObjectId):
    """Soft delete a device"""
    device = await Device.get(device_id)
    
    if not device or not device.is_active:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await device.update({"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
    return {"message": "Device deleted successfully"}


# Energy data endpoints
@router.post("/devices/{device_id}/energy-data/", response_model=EnergyDataSchema)
async def create_energy_data(device_id: PydanticObjectId, energy_data: EnergyDataCreate):
    """Create new energy data for a device"""
    device = await Device.get(device_id)
    
    if not device or not device.is_active:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update device last_seen
    await device.update({"$set": {"last_seen": datetime.utcnow()}})
    
    # Create energy data
    energy_data_dict = energy_data.model_dump()
    energy_data_dict["user_id"] = device.user_id
    energy_data_dict["device_id"] = device_id
    
    db_energy_data = EnergyData(**energy_data_dict)
    await db_energy_data.insert()
    return db_energy_data


@router.get("/devices/{device_id}/energy-data/", response_model=List[EnergyDataSchema])
async def get_device_energy_data(
    device_id: PydanticObjectId,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get energy data for a device with optional date filtering"""
    query = {"device_id": device_id}
    
    if start_date or end_date:
        timestamp_filter = {}
        if start_date:
            timestamp_filter["$gte"] = start_date
        if end_date:
            timestamp_filter["$lte"] = end_date
        query["timestamp"] = timestamp_filter
    
    energy_data = await EnergyData.find(query).sort([("timestamp", -1)]).skip(skip).limit(limit).to_list()
    return energy_data


@router.get("/users/{user_id}/energy-data/", response_model=List[EnergyDataSchema])
async def get_user_energy_data(
    user_id: PydanticObjectId,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all energy data for a user with optional date filtering"""
    query = {"user_id": user_id}
    
    if start_date or end_date:
        timestamp_filter = {}
        if start_date:
            timestamp_filter["$gte"] = start_date
        if end_date:
            timestamp_filter["$lte"] = end_date
        query["timestamp"] = timestamp_filter
    
    energy_data = await EnergyData.find(query).sort([("timestamp", -1)]).skip(skip).limit(limit).to_list()
    return energy_data


@router.get("/users/{user_id}/energy-stats/", response_model=EnergyStats)
async def get_user_energy_stats(
    user_id: PydanticObjectId,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get energy statistics for a user"""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # MongoDB aggregation pipeline
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_consumption": {"$sum": "$consumption_kwh"},
                "total_production": {"$sum": "$production_kwh"},
                "total_cost": {"$sum": "$cost_usd"},
                "avg_power": {"$avg": "$power_watts"},
                "peak_power": {"$max": "$power_watts"},
                "device_count": {"$addToSet": "$device_id"}
            }
        },
        {
            "$project": {
                "total_consumption": 1,
                "total_production": 1,
                "total_cost": 1,
                "avg_power": 1,
                "peak_power": 1,
                "device_count": {"$size": "$device_count"}
            }
        }
    ]
    
    result = await EnergyData.aggregate(pipeline).to_list(length=1)
    
    if not result:
        stats_data = {
            "total_consumption_kwh": 0.0,
            "total_production_kwh": 0.0,
            "total_cost_usd": 0.0,
            "average_power_watts": None,
            "peak_power_watts": None,
            "device_count": 0
        }
    else:
        stats = result[0]
        stats_data = {
            "total_consumption_kwh": stats.get("total_consumption", 0.0),
            "total_production_kwh": stats.get("total_production", 0.0),
            "total_cost_usd": stats.get("total_cost", 0.0),
            "average_power_watts": stats.get("avg_power"),
            "peak_power_watts": stats.get("peak_power"),
            "device_count": stats.get("device_count", 0)
        }
    
    return EnergyStats(
        period_start=start_date,
        period_end=end_date,
        **stats_data
    )


@router.get("/users/{user_id}/daily-stats/", response_model=List[DailyEnergyStats])
async def get_user_daily_stats(
    user_id: PydanticObjectId,
    days: int = Query(30, ge=1, le=365)
):
    """Get daily energy statistics for a user"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # MongoDB aggregation pipeline for daily stats
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp"
                    }
                },
                "consumption": {"$sum": "$consumption_kwh"},
                "production": {"$sum": "$production_kwh"},
                "cost": {"$sum": "$cost_usd"},
                "avg_temp": {"$avg": "$temperature_celsius"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    result = await EnergyData.aggregate(pipeline).to_list(length=None)
    
    daily_stats = []
    for row in result:
        daily_stats.append(DailyEnergyStats(
            date=row["_id"],
            consumption_kwh=row.get("consumption", 0.0),
            production_kwh=row.get("production", 0.0),
            cost_usd=row.get("cost", 0.0),
            average_temperature=row.get("avg_temp")
        ))
    
    return daily_stats