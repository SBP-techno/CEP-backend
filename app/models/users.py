from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    energy_goal_kwh: Optional[float] = Field(default=1000.0, description="Monthly energy goal in kWh")
    preferred_energy_source: Optional[str] = Field(default="mixed", description="Preferred energy source")
    notifications_enabled: bool = Field(default=True)
    timezone: str = Field(default="UTC")


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    energy_goal_kwh: Optional[float] = None
    preferred_energy_source: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    timezone: Optional[str] = None


class UserInDB(UserBase):
    """User model for database operations"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    device_count: int = Field(default=0)
    total_energy_consumed: float = Field(default=0.0)
    total_energy_produced: float = Field(default=0.0)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserResponse(UserBase):
    """User response model"""
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    device_count: int
    total_energy_consumed: float
    total_energy_produced: float

    class Config:
        json_encoders = {ObjectId: str}