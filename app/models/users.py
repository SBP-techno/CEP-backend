from beanie import Document, Indexed
from pydantic import Field, EmailStr
from datetime import datetime
from typing import Optional
from pymongo import IndexModel


class User(Document):
    """User document model for MongoDB"""
    
    # Basic user information
    email: Indexed(EmailStr, unique=True) = Field(..., description="User email address")
    username: Indexed(str, unique=True) = Field(..., min_length=1, max_length=100, description="Unique username")
    full_name: Optional[str] = Field(None, max_length=200, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    # Energy conservation preferences
    energy_goal_kwh: Optional[float] = Field(None, ge=0, description="Monthly energy goal in kWh")
    preferred_temperature: Optional[float] = Field(None, description="Preferred room temperature in Celsius")
    
    class Settings:
        name = "users"  # Collection name
        indexes = [
            IndexModel("email", unique=True),
            IndexModel("username", unique=True),
            IndexModel("is_active"),
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "energy_goal_kwh": 300.0,
                "preferred_temperature": 22.0
            }
        }