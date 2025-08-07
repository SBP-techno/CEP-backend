from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum
from pymongo import IndexModel


class DeviceType(str, Enum):
    """Device type enumeration"""
    HVAC = "hvac"
    LIGHTING = "lighting"
    APPLIANCE = "appliance"
    WATER_HEATER = "water_heater"
    SOLAR_PANEL = "solar_panel"
    SMART_METER = "smart_meter"
    OTHER = "other"


class Device(Document):
    """Device document model for MongoDB"""
    
    # Reference to user
    user_id: PydanticObjectId = Field(..., description="Reference to the user who owns this device")
    
    # Device information
    name: str = Field(..., min_length=1, max_length=200, description="Device name")
    device_type: DeviceType = Field(..., description="Type of device")
    model: Optional[str] = Field(None, max_length=200, description="Device model")
    manufacturer: Optional[str] = Field(None, max_length=200, description="Device manufacturer")
    location: Optional[str] = Field(None, max_length=200, description="Room or area where device is located")
    
    # Device specifications
    rated_power_watts: Optional[float] = Field(None, ge=0, description="Rated power consumption in watts")
    is_smart_device: bool = Field(default=False, description="Whether device can be controlled remotely")
    is_active: bool = Field(default=True, description="Whether the device is active")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Device creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    last_seen: Optional[datetime] = Field(default=None, description="Last time device was seen/active")
    
    class Settings:
        name = "devices"  # Collection name
        indexes = [
            IndexModel("user_id"),
            IndexModel("device_type"),
            IndexModel("is_active"),
            IndexModel([("user_id", 1), ("is_active", 1)]),
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Living Room AC",
                "device_type": "hvac",
                "model": "EcoAir 2000",
                "manufacturer": "EcoTech",
                "location": "Living Room",
                "rated_power_watts": 2000.0,
                "is_smart_device": True
            }
        }