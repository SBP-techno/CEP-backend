from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Energy conservation preferences
    energy_goal_kwh = Column(Float, nullable=True)  # Monthly energy goal in kWh
    preferred_temperature = Column(Float, nullable=True)  # Preferred room temperature
    
    # Relationships
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    energy_data = relationship("EnergyData", back_populates="user", cascade="all, delete-orphan")