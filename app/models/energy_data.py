from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional
from pymongo import IndexModel


class EnergyData(Document):
    """Energy data document model for storing consumption and production data"""
    
    # References
    user_id: PydanticObjectId = Field(..., description="Reference to the user")
    device_id: PydanticObjectId = Field(..., description="Reference to the device")
    
    # Energy measurements
    consumption_kwh: float = Field(default=0.0, ge=0, description="Energy consumed in kWh")
    production_kwh: float = Field(default=0.0, ge=0, description="Energy produced in kWh (for solar panels)")
    power_watts: Optional[float] = Field(None, description="Instantaneous power in watts")
    voltage: Optional[float] = Field(None, description="Voltage measurement")
    current_amps: Optional[float] = Field(None, description="Current measurement in amps")
    
    # Environmental data
    temperature_celsius: Optional[float] = Field(None, description="Temperature at device location")
    humidity_percent: Optional[float] = Field(None, ge=0, le=100, description="Humidity percentage")
    
    # Cost calculation
    cost_usd: Optional[float] = Field(None, ge=0, description="Cost in USD based on consumption")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the measurement")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    
    class Settings:
        name = "energy_data"  # Collection name
        indexes = [
            IndexModel("user_id"),
            IndexModel("device_id"),
            IndexModel("timestamp"),
            IndexModel([("user_id", 1), ("timestamp", -1)]),
            IndexModel([("device_id", 1), ("timestamp", -1)]),
            IndexModel([("user_id", 1), ("device_id", 1), ("timestamp", -1)]),
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "consumption_kwh": 1.25,
                "production_kwh": 0.0,
                "power_watts": 1800.0,
                "voltage": 120.0,
                "current_amps": 15.0,
                "temperature_celsius": 22.5,
                "humidity_percent": 45.0,
                "cost_usd": 0.15,
                "timestamp": "2024-01-15T10:30:00"
            }
        }