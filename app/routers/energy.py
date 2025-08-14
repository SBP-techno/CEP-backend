from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import logging

from app.database import get_database
from app.models.users import UserCreate, UserUpdate, UserResponse, UserInDB
from app.models.devices import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceInDB
from app.models.energy_data import (
    EnergyDataCreate, EnergyDataUpdate, EnergyDataResponse, EnergyDataInDB,
    EnergyStats, DailyEnergyStats
)
from app.schemas.energy import (
    UserListResponse, DeviceListResponse, EnergyDataListResponse,
    UserWithDevicesResponse, DeviceWithEnergyDataResponse,
    PaginationParams, SuccessResponse, ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Helper functions
def get_db():
    """Get database instance"""
    return get_database()


async def get_user_by_id(user_id: str, db) -> Optional[dict]:
    """Get user by ID"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


async def get_device_by_id(device_id: str, db) -> Optional[dict]:
    """Get device by ID"""
    try:
        device = await db.devices.find_one({"_id": ObjectId(device_id)})
        return device
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return None


# User endpoints
@router.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db=Depends(get_db)):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({
            "$or": [
                {"email": user.email},
                {"username": user.username}
            ]
        })
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email or username already exists")
        
        # Create user document
        user_data = user.dict()
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        user_data["is_active"] = True
        user_data["device_count"] = 0
        user_data["total_energy_consumed"] = 0.0
        user_data["total_energy_produced"] = 0.0
        
        result = await db.users.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """List all users with pagination"""
    try:
        total = await db.users.count_documents({})
        users = await db.users.find({}).skip(skip).limit(limit).to_list(length=limit)
        
        user_responses = [UserResponse(**user) for user in users]
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}", response_model=UserWithDevicesResponse)
async def get_user(user_id: str, db=Depends(get_db)):
    """Get user by ID with associated devices"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's devices
        devices = await db.devices.find({"user_id": user_id}).to_list(length=None)
        device_responses = [DeviceResponse(**device) for device in devices]
        
        user_response = UserResponse(**user)
        return UserWithDevicesResponse(**user_response.dict(), devices=device_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, db=Depends(get_db)):
    """Update user information"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = user_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made")
        
        # Get updated user
        updated_user = await get_user_by_id(user_id, db)
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user(user_id: str, db=Depends(get_db)):
    """Delete user and all associated data"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user's devices and energy data
        await db.devices.delete_many({"user_id": user_id})
        await db.energy_data.delete_many({"user_id": user_id})
        await db.users.delete_one({"_id": ObjectId(user_id)})
        
        return SuccessResponse(message="User and all associated data deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Device endpoints
@router.post("/users/{user_id}/devices/", response_model=DeviceResponse)
async def create_device(user_id: str, device: DeviceCreate, db=Depends(get_db)):
    """Create a new device for a user"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create device document
        device_data = device.dict()
        device_data["user_id"] = user_id
        device_data["created_at"] = datetime.utcnow()
        device_data["updated_at"] = datetime.utcnow()
        device_data["is_active"] = True
        device_data["total_energy_consumed"] = 0.0
        device_data["total_energy_produced"] = 0.0
        device_data["current_power_draw"] = 0.0
        
        result = await db.devices.insert_one(device_data)
        device_data["_id"] = result.inserted_id
        
        # Update user's device count
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"device_count": 1}}
        )
        
        return DeviceResponse(**device_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}/devices/", response_model=DeviceListResponse)
async def list_user_devices(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """List all devices for a user"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        total = await db.devices.count_documents({"user_id": user_id})
        devices = await db.devices.find({"user_id": user_id}).skip(skip).limit(limit).to_list(length=limit)
        
        device_responses = [DeviceResponse(**device) for device in devices]
        
        return DeviceListResponse(
            devices=device_responses,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing devices for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/devices/{device_id}", response_model=DeviceWithEnergyDataResponse)
async def get_device(device_id: str, db=Depends(get_db)):
    """Get device by ID with recent energy data"""
    try:
        device = await get_device_by_id(device_id, db)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get recent energy data (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_data = await db.energy_data.find({
            "device_id": device_id,
            "timestamp": {"$gte": yesterday}
        }).sort("timestamp", -1).limit(10).to_list(length=10)
        
        energy_data_responses = [EnergyDataResponse(**data) for data in recent_data]
        
        device_response = DeviceResponse(**device)
        return DeviceWithEnergyDataResponse(
            **device_response.dict(),
            recent_energy_data=energy_data_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: str, device_update: DeviceUpdate, db=Depends(get_db)):
    """Update device information"""
    try:
        device = await get_device_by_id(device_id, db)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Prepare update data
        update_data = device_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.devices.update_one(
            {"_id": ObjectId(device_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made")
        
        # Get updated device
        updated_device = await get_device_by_id(device_id, db)
        return DeviceResponse(**updated_device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/devices/{device_id}", response_model=SuccessResponse)
async def delete_device(device_id: str, db=Depends(get_db)):
    """Delete device and all associated energy data"""
    try:
        device = await get_device_by_id(device_id, db)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Delete device's energy data
        await db.energy_data.delete_many({"device_id": device_id})
        await db.devices.delete_one({"_id": ObjectId(device_id)})
        
        # Update user's device count
        await db.users.update_one(
            {"_id": ObjectId(device["user_id"])},
            {"$inc": {"device_count": -1}}
        )
        
        return SuccessResponse(message="Device and all associated data deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Energy data endpoints
@router.post("/devices/{device_id}/energy-data/", response_model=EnergyDataResponse)
async def create_energy_data(device_id: str, energy_data: EnergyDataCreate, db=Depends(get_db)):
    """Create new energy data for a device"""
    try:
        device = await get_device_by_id(device_id, db)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create energy data document
        data = energy_data.dict()
        data["device_id"] = device_id
        data["user_id"] = device["user_id"]
        data["timestamp"] = data.get("timestamp", datetime.utcnow())
        data["created_at"] = datetime.utcnow()
        
        result = await db.energy_data.insert_one(data)
        data["_id"] = result.inserted_id
        
        # Update device statistics
        await db.devices.update_one(
            {"_id": ObjectId(device_id)},
            {
                "$inc": {
                    "total_energy_consumed": data["energy_consumption_kwh"],
                    "total_energy_produced": data["energy_production_kwh"]
                },
                "$set": {
                    "current_power_draw": data["power_consumption_watts"],
                    "last_energy_reading": data["timestamp"]
                }
            }
        )
        
        # Update user statistics
        await db.users.update_one(
            {"_id": ObjectId(device["user_id"])},
            {
                "$inc": {
                    "total_energy_consumed": data["energy_consumption_kwh"],
                    "total_energy_produced": data["energy_production_kwh"]
                }
            }
        )
        
        return EnergyDataResponse(**data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating energy data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/devices/{device_id}/energy-data/", response_model=EnergyDataListResponse)
async def get_device_energy_data(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db=Depends(get_db)
):
    """Get energy data for a device"""
    try:
        device = await get_device_by_id(device_id, db)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Build query
        query = {"device_id": device_id}
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        total = await db.energy_data.count_documents(query)
        data = await db.energy_data.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(length=limit)
        
        energy_data_responses = [EnergyDataResponse(**item) for item in data]
        
        return EnergyDataListResponse(
            energy_data=energy_data_responses,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting energy data for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}/energy-data/", response_model=EnergyDataListResponse)
async def get_user_energy_data(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db=Depends(get_db)
):
    """Get energy data for a user"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build query
        query = {"user_id": user_id}
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        total = await db.energy_data.count_documents(query)
        data = await db.energy_data.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(length=limit)
        
        energy_data_responses = [EnergyDataResponse(**item) for item in data]
        
        return EnergyDataListResponse(
            energy_data=energy_data_responses,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting energy data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Statistics endpoints
@router.get("/users/{user_id}/energy-stats/", response_model=EnergyStats)
async def get_user_energy_stats(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db=Depends(get_db)
):
    """Get energy statistics for a user"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Set default date range (last 30 days)
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build aggregation pipeline
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
                    "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                    "total_energy_produced": {"$sum": "$energy_production_kwh"},
                    "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                    "average_power_consumption": {"$avg": "$power_consumption_watts"},
                    "peak_power_consumption": {"$max": "$power_consumption_watts"},
                    "data_points_count": {"$sum": 1}
                }
            }
        ]
        
        result = list(await db.energy_data.aggregate(pipeline))
        
        if not result:
            # Return empty stats if no data
            return EnergyStats(
                total_energy_consumed=0.0,
                total_energy_produced=0.0,
                total_cost=0.0,
                average_power_consumption=0.0,
                peak_power_consumption=0.0,
                period_start=start_date,
                period_end=end_date,
                data_points_count=0
            )
        
        stats = result[0]
        return EnergyStats(
            total_energy_consumed=stats["total_energy_consumed"],
            total_energy_produced=stats["total_energy_produced"],
            total_cost=stats["total_cost"],
            average_power_consumption=stats["average_power_consumption"],
            peak_power_consumption=stats["peak_power_consumption"],
            period_start=start_date,
            period_end=end_date,
            data_points_count=stats["data_points_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting energy stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}/daily-stats/", response_model=List[DailyEnergyStats])
async def get_user_daily_stats(
    user_id: str,
    days: int = Query(7, ge=1, le=30),
    db=Depends(get_db)
):
    """Get daily energy statistics for a user"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build aggregation pipeline for daily stats
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
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"},
                        "day": {"$dayOfMonth": "$timestamp"}
                    },
                    "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                    "total_energy_produced": {"$sum": "$energy_production_kwh"},
                    "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                    "average_power_consumption": {"$avg": "$power_consumption_watts"},
                    "peak_power_consumption": {"$max": "$power_consumption_watts"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        result = await db.energy_data.aggregate(pipeline).to_list(length=None)
        
        daily_stats = []
        for item in result:
            date_str = f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}"
            daily_stats.append(DailyEnergyStats(
                date=date_str,
                total_energy_consumed=item["total_energy_consumed"],
                total_energy_produced=item["total_energy_produced"],
                total_cost=item["total_cost"],
                average_power_consumption=item["average_power_consumption"],
                peak_power_consumption=item["peak_power_consumption"]
            ))
        
        return daily_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")