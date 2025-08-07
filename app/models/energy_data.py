from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class EnergyData(Base):
    """Energy data model for storing consumption and production data"""
    __tablename__ = "energy_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    
    # Energy measurements
    consumption_kwh = Column(Float, nullable=False, default=0.0)  # Energy consumed in kWh
    production_kwh = Column(Float, nullable=False, default=0.0)   # Energy produced in kWh (for solar panels)
    power_watts = Column(Float, nullable=True)                    # Instantaneous power in watts
    voltage = Column(Float, nullable=True)                        # Voltage measurement
    current_amps = Column(Float, nullable=True)                   # Current measurement in amps
    
    # Environmental data
    temperature_celsius = Column(Float, nullable=True)            # Temperature at device location
    humidity_percent = Column(Float, nullable=True)               # Humidity percentage
    
    # Cost calculation
    cost_usd = Column(Float, nullable=True)                       # Cost in USD based on consumption
    
    # Timestamp for the measurement
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="energy_data")
    device = relationship("Device", back_populates="energy_data")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_energy_data_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_energy_data_device_timestamp', 'device_id', 'timestamp'),
        Index('idx_energy_data_timestamp', 'timestamp'),
    )