from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class DeviceType(enum.Enum):
    """Device type enumeration"""
    HVAC = "hvac"
    LIGHTING = "lighting"
    APPLIANCE = "appliance"
    WATER_HEATER = "water_heater"
    SOLAR_PANEL = "solar_panel"
    SMART_METER = "smart_meter"
    OTHER = "other"


class Device(Base):
    """Device model for energy monitoring"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Device information
    name = Column(String(200), nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    model = Column(String(200), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)  # Room or area where device is located
    
    # Device specifications
    rated_power_watts = Column(Float, nullable=True)  # Rated power consumption in watts
    is_smart_device = Column(Boolean, default=False)  # Whether device can be controlled remotely
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="devices")
    energy_data = relationship("EnergyData", back_populates="device", cascade="all, delete-orphan")