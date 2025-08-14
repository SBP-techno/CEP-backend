from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.users import PyObjectId


class EnergyDataBase(BaseModel):
    """Base energy data model"""
    device_id: str = Field(..., description="ID of the device")
    user_id: str = Field(..., description="ID of the user")
    power_consumption_watts: float = Field(..., description="Power consumption in watts")
    energy_consumption_kwh: float = Field(..., description="Energy consumption in kWh")
    energy_production_kwh: float = Field(default=0.0, description="Energy production in kWh (for solar panels)")
    voltage: Optional[float] = Field(None, description="Voltage reading")
    current: Optional[float] = Field(None, description="Current reading in amps")
    power_factor: Optional[float] = Field(None, description="Power factor")
    temperature: Optional[float] = Field(None, description="Temperature reading")
    humidity: Optional[float] = Field(None, description="Humidity reading")
    cost_per_kwh: Optional[float] = Field(None, description="Cost per kWh")
    total_cost: Optional[float] = Field(None, description="Total cost for this reading")
    data_source: str = Field(default="manual", description="Source of data (manual, sensor, api)")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EnergyDataCreate(EnergyDataBase):
    """Energy data creation model"""
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class EnergyDataUpdate(BaseModel):
    """Energy data update model"""
    power_consumption_watts: Optional[float] = None
    energy_consumption_kwh: Optional[float] = None
    energy_production_kwh: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    cost_per_kwh: Optional[float] = None
    total_cost: Optional[float] = None
    data_source: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class EnergyDataInDB(EnergyDataBase):
    """Energy data model for database operations"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class EnergyDataResponse(EnergyDataBase):
    """Energy data response model"""
    id: str
    timestamp: datetime
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}


class EnergyStats(BaseModel):
    """Energy statistics model"""
    total_energy_consumed: float
    total_energy_produced: float
    total_cost: float
    average_power_consumption: float
    peak_power_consumption: float
    energy_efficiency_score: Optional[float] = None
    carbon_footprint_kg: Optional[float] = None
    period_start: datetime
    period_end: datetime
    data_points_count: int


class DailyEnergyStats(BaseModel):
    """Daily energy statistics model"""
    date: str
    total_energy_consumed: float
    total_energy_produced: float
    total_cost: float
    average_power_consumption: float
    peak_power_consumption: float
    device_breakdown: Dict[str, float] = Field(default_factory=dict)
    hourly_breakdown: Dict[str, float] = Field(default_factory=dict)