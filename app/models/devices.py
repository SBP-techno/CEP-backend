from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.users import PyObjectId


class DeviceBase(BaseModel):
    """Base device model"""
    name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(..., description="Type of device (hvac, lighting, appliance, solar, etc.)")
    location: Optional[str] = Field(None, max_length=200)
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    power_rating_watts: Optional[float] = Field(None, description="Device power rating in watts")
    is_smart_device: bool = Field(default=False)
    is_active: bool = Field(default=True)
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DeviceCreate(DeviceBase):
    """Device creation model"""
    user_id: str = Field(..., description="ID of the user who owns this device")


class DeviceUpdate(BaseModel):
    """Device update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_type: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    power_rating_watts: Optional[float] = None
    is_smart_device: Optional[bool] = None
    is_active: Optional[bool] = None
    specifications: Optional[Dict[str, Any]] = None


class DeviceInDB(DeviceBase):
    """Device model for database operations"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_energy_reading: Optional[datetime] = None
    total_energy_consumed: float = Field(default=0.0)
    total_energy_produced: float = Field(default=0.0)
    current_power_draw: float = Field(default=0.0)
    efficiency_rating: Optional[float] = Field(None, description="Device efficiency rating (0-100)")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DeviceResponse(DeviceBase):
    """Device response model"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_energy_reading: Optional[datetime]
    total_energy_consumed: float
    total_energy_produced: float
    current_power_draw: float
    efficiency_rating: Optional[float]

    class Config:
        json_encoders = {ObjectId: str}


class DeviceWithEnergyData(DeviceResponse):
    """Device model with energy data"""
    recent_energy_data: Optional[list] = Field(default_factory=list)
    daily_energy_consumption: Optional[float] = None
    monthly_energy_consumption: Optional[float] = None