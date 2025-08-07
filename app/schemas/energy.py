from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum
from beanie import PydanticObjectId

from app.models.devices import DeviceType


# Base schemas
class EnergyDataBase(BaseModel):
    """Base schema for energy data"""
    consumption_kwh: float = Field(ge=0, description="Energy consumed in kWh")
    production_kwh: float = Field(ge=0, default=0.0, description="Energy produced in kWh")
    power_watts: Optional[float] = Field(None, description="Instantaneous power in watts")
    voltage: Optional[float] = Field(None, description="Voltage measurement")
    current_amps: Optional[float] = Field(None, description="Current measurement in amps")
    temperature_celsius: Optional[float] = Field(None, description="Temperature at device location")
    humidity_percent: Optional[float] = Field(None, ge=0, le=100, description="Humidity percentage")
    cost_usd: Optional[float] = Field(None, ge=0, description="Cost in USD")
    timestamp: datetime = Field(description="Timestamp of the measurement")


class EnergyDataCreate(EnergyDataBase):
    """Schema for creating energy data"""
    device_id: PydanticObjectId = Field(description="ID of the device")


class EnergyDataUpdate(BaseModel):
    """Schema for updating energy data"""
    consumption_kwh: Optional[float] = Field(None, ge=0)
    production_kwh: Optional[float] = Field(None, ge=0)
    power_watts: Optional[float] = None
    voltage: Optional[float] = None
    current_amps: Optional[float] = None
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = Field(None, ge=0, le=100)
    cost_usd: Optional[float] = Field(None, ge=0)


class EnergyData(EnergyDataBase):
    """Schema for energy data response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: PydanticObjectId
    user_id: PydanticObjectId
    device_id: PydanticObjectId
    created_at: datetime


# Device schemas
class DeviceBase(BaseModel):
    """Base schema for device"""
    name: str = Field(min_length=1, max_length=200, description="Device name")
    device_type: DeviceType = Field(description="Type of device")
    model: Optional[str] = Field(None, max_length=200, description="Device model")
    manufacturer: Optional[str] = Field(None, max_length=200, description="Device manufacturer")
    location: Optional[str] = Field(None, max_length=200, description="Device location")
    rated_power_watts: Optional[float] = Field(None, ge=0, description="Rated power in watts")
    is_smart_device: bool = Field(default=False, description="Whether device is smart")


class DeviceCreate(DeviceBase):
    """Schema for creating device"""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating device"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    device_type: Optional[DeviceType] = None
    model: Optional[str] = Field(None, max_length=200)
    manufacturer: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    rated_power_watts: Optional[float] = Field(None, ge=0)
    is_smart_device: Optional[bool] = None
    is_active: Optional[bool] = None


class Device(DeviceBase):
    """Schema for device response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: PydanticObjectId
    user_id: PydanticObjectId
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_seen: Optional[datetime]


class DeviceWithEnergyData(Device):
    """Device schema with recent energy data"""
    recent_energy_data: List[EnergyData] = Field(default_factory=list)


# User schemas
class UserBase(BaseModel):
    """Base schema for user"""
    email: str = Field(description="User email")
    username: str = Field(min_length=1, max_length=100, description="Username")
    full_name: Optional[str] = Field(None, max_length=200, description="Full name")
    energy_goal_kwh: Optional[float] = Field(None, ge=0, description="Monthly energy goal in kWh")
    preferred_temperature: Optional[float] = Field(None, description="Preferred temperature")


class UserCreate(UserBase):
    """Schema for creating user"""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user"""
    email: Optional[str] = None
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)
    energy_goal_kwh: Optional[float] = Field(None, ge=0)
    preferred_temperature: Optional[float] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Schema for user response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: PydanticObjectId
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class UserWithDevices(User):
    """User schema with devices"""
    devices: List[Device] = Field(default_factory=list)


# Energy statistics schemas
class EnergyStats(BaseModel):
    """Schema for energy statistics"""
    total_consumption_kwh: float
    total_production_kwh: float
    total_cost_usd: float
    average_power_watts: Optional[float]
    peak_power_watts: Optional[float]
    period_start: datetime
    period_end: datetime
    device_count: int


class DailyEnergyStats(BaseModel):
    """Schema for daily energy statistics"""
    date: str
    consumption_kwh: float
    production_kwh: float
    cost_usd: float
    average_temperature: Optional[float]