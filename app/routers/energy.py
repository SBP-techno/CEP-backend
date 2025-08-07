from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
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
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user"""
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.email == user.email) | (User.username == user.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get("/users/", response_model=List[UserSchema])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination"""
    result = await db.execute(
        select(User).where(User.is_active == True).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserWithDevices)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get a user by ID with their devices"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a user"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Soft delete a user"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    await db.commit()
    return {"message": "User deleted successfully"}


# Device endpoints
@router.post("/users/{user_id}/devices/", response_model=DeviceSchema)
async def create_device(
    user_id: int,
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device for a user"""
    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_device = Device(user_id=user_id, **device.model_dump())
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.get("/users/{user_id}/devices/", response_model=List[DeviceSchema])
async def get_user_devices(
    user_id: int,
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get all devices for a user"""
    query = select(Device).where(Device.user_id == user_id)
    
    if not include_inactive:
        query = query.where(Device.is_active == True)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/devices/{device_id}", response_model=DeviceWithEnergyData)
async def get_device(
    device_id: int,
    include_recent_data: bool = Query(True),
    data_hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_db)
):
    """Get a device by ID with optional recent energy data"""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_active == True)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device_dict = DeviceSchema.model_validate(device).model_dump()
    
    if include_recent_data:
        # Get recent energy data
        since = datetime.utcnow() - timedelta(hours=data_hours)
        result = await db.execute(
            select(EnergyData)
            .where(
                and_(
                    EnergyData.device_id == device_id,
                    EnergyData.timestamp >= since
                )
            )
            .order_by(desc(EnergyData.timestamp))
            .limit(100)
        )
        recent_data = result.scalars().all()
        device_dict["recent_energy_data"] = recent_data
    
    return DeviceWithEnergyData(**device_dict)


@router.put("/devices/{device_id}", response_model=DeviceSchema)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a device"""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_active == True)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update only provided fields
    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/devices/{device_id}")
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Soft delete a device"""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_active == True)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.is_active = False
    await db.commit()
    return {"message": "Device deleted successfully"}


# Energy data endpoints
@router.post("/devices/{device_id}/energy-data/", response_model=EnergyDataSchema)
async def create_energy_data(
    device_id: int,
    energy_data: EnergyDataCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new energy data for a device"""
    # Verify device exists
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_active == True)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update device last_seen
    device.last_seen = datetime.utcnow()
    
    # Create energy data
    energy_data_dict = energy_data.model_dump()
    energy_data_dict.pop('device_id', None)  # Remove device_id from the dict
    
    db_energy_data = EnergyData(
        user_id=device.user_id,
        device_id=device_id,
        **energy_data_dict
    )
    
    db.add(db_energy_data)
    await db.commit()
    await db.refresh(db_energy_data)
    return db_energy_data


@router.get("/devices/{device_id}/energy-data/", response_model=List[EnergyDataSchema])
async def get_device_energy_data(
    device_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get energy data for a device with optional date filtering"""
    query = select(EnergyData).where(EnergyData.device_id == device_id)
    
    if start_date:
        query = query.where(EnergyData.timestamp >= start_date)
    if end_date:
        query = query.where(EnergyData.timestamp <= end_date)
    
    query = query.order_by(desc(EnergyData.timestamp)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/users/{user_id}/energy-data/", response_model=List[EnergyDataSchema])
async def get_user_energy_data(
    user_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get all energy data for a user with optional date filtering"""
    query = select(EnergyData).where(EnergyData.user_id == user_id)
    
    if start_date:
        query = query.where(EnergyData.timestamp >= start_date)
    if end_date:
        query = query.where(EnergyData.timestamp <= end_date)
    
    query = query.order_by(desc(EnergyData.timestamp)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/users/{user_id}/energy-stats/", response_model=EnergyStats)
async def get_user_energy_stats(
    user_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get energy statistics for a user"""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get aggregated data
    result = await db.execute(
        select(
            func.sum(EnergyData.consumption_kwh).label("total_consumption"),
            func.sum(EnergyData.production_kwh).label("total_production"),
            func.sum(EnergyData.cost_usd).label("total_cost"),
            func.avg(EnergyData.power_watts).label("avg_power"),
            func.max(EnergyData.power_watts).label("peak_power"),
            func.count(func.distinct(EnergyData.device_id)).label("device_count")
        ).where(
            and_(
                EnergyData.user_id == user_id,
                EnergyData.timestamp >= start_date,
                EnergyData.timestamp <= end_date
            )
        )
    )
    
    stats = result.first()
    
    return EnergyStats(
        total_consumption_kwh=stats.total_consumption or 0.0,
        total_production_kwh=stats.total_production or 0.0,
        total_cost_usd=stats.total_cost or 0.0,
        average_power_watts=stats.avg_power,
        peak_power_watts=stats.peak_power,
        period_start=start_date,
        period_end=end_date,
        device_count=stats.device_count or 0
    )


@router.get("/users/{user_id}/daily-stats/", response_model=List[DailyEnergyStats])
async def get_user_daily_stats(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get daily energy statistics for a user"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.date(EnergyData.timestamp).label("date"),
            func.sum(EnergyData.consumption_kwh).label("consumption"),
            func.sum(EnergyData.production_kwh).label("production"),
            func.sum(EnergyData.cost_usd).label("cost"),
            func.avg(EnergyData.temperature_celsius).label("avg_temp")
        ).where(
            and_(
                EnergyData.user_id == user_id,
                EnergyData.timestamp >= start_date,
                EnergyData.timestamp <= end_date
            )
        ).group_by(
            func.date(EnergyData.timestamp)
        ).order_by(
            func.date(EnergyData.timestamp)
        )
    )
    
    daily_stats = []
    for row in result:
        daily_stats.append(DailyEnergyStats(
            date=row.date.isoformat(),
            consumption_kwh=row.consumption or 0.0,
            production_kwh=row.production or 0.0,
            cost_usd=row.cost or 0.0,
            average_temperature=row.avg_temp
        ))
    
    return daily_stats