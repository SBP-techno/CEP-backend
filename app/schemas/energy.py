from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

# Import models
from app.models.users import UserCreate, UserUpdate, UserResponse, UserInDB
from app.models.devices import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceInDB, DeviceWithEnergyData
from app.models.energy_data import (
    EnergyDataCreate, EnergyDataUpdate, EnergyDataResponse, EnergyDataInDB,
    EnergyStats, DailyEnergyStats
)


# Response schemas for API endpoints
class UserListResponse(BaseModel):
    """Response schema for user list"""
    users: List[UserResponse]
    total: int
    page: int
    size: int


class DeviceListResponse(BaseModel):
    """Response schema for device list"""
    devices: List[DeviceResponse]
    total: int
    page: int
    size: int


class EnergyDataListResponse(BaseModel):
    """Response schema for energy data list"""
    energy_data: List[EnergyDataResponse]
    total: int
    page: int
    size: int


class UserWithDevicesResponse(UserResponse):
    """User response with associated devices"""
    devices: List[DeviceResponse] = []


class DeviceWithEnergyDataResponse(DeviceResponse):
    """Device response with recent energy data"""
    recent_energy_data: List[EnergyDataResponse] = []
    daily_energy_consumption: Optional[float] = None
    monthly_energy_consumption: Optional[float] = None


# Statistics and analytics schemas
class EnergyComparisonRequest(BaseModel):
    """Request schema for energy comparison"""
    start_date: datetime
    end_date: datetime
    comparison_start_date: Optional[datetime] = None
    comparison_end_date: Optional[datetime] = None
    device_ids: Optional[List[str]] = None


class EnergyComparisonResponse(BaseModel):
    """Response schema for energy comparison"""
    current_period: EnergyStats
    comparison_period: Optional[EnergyStats] = None
    percentage_change: Optional[float] = None
    cost_savings: Optional[float] = None
    energy_savings: Optional[float] = None


class DeviceEfficiencyReport(BaseModel):
    """Device efficiency report"""
    device_id: str
    device_name: str
    device_type: str
    efficiency_score: float
    energy_consumption: float
    cost: float
    recommendations: List[str]
    potential_savings: Optional[float] = None


class UserEfficiencyReport(BaseModel):
    """User efficiency report"""
    user_id: str
    overall_efficiency_score: float
    total_energy_consumed: float
    total_cost: float
    device_reports: List[DeviceEfficiencyReport]
    recommendations: List[str]
    potential_monthly_savings: float


# AI Recommendation schemas
class AIRecommendationRequest(BaseModel):
    """Request schema for AI recommendations"""
    user_id: str
    analysis_type: str = Field(..., description="Type of analysis (general, device_specific, comparison)")
    device_id: Optional[str] = None
    time_period: Optional[str] = Field(None, description="Time period for analysis (week, month, year)")
    include_cost_analysis: bool = Field(default=True)
    include_efficiency_tips: bool = Field(default=True)


class AIRecommendationResponse(BaseModel):
    """Response schema for AI recommendations"""
    user_id: str
    analysis_type: str
    recommendations: List[str]
    energy_savings_potential: Optional[float] = None
    cost_savings_potential: Optional[float] = None
    efficiency_score: Optional[float] = None
    device_specific_tips: Optional[Dict[str, List[str]]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class EnergyAnalysisRequest(BaseModel):
    """Request schema for energy pattern analysis"""
    user_id: str
    start_date: datetime
    end_date: datetime
    analysis_type: str = Field(..., description="Type of analysis (patterns, anomalies, trends)")
    device_ids: Optional[List[str]] = None


class EnergyAnalysisResponse(BaseModel):
    """Response schema for energy pattern analysis"""
    user_id: str
    analysis_type: str
    patterns_found: List[Dict[str, Any]]
    anomalies_detected: List[Dict[str, Any]]
    trends_identified: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Dashboard and summary schemas
class DashboardSummary(BaseModel):
    """Dashboard summary data"""
    total_energy_consumed_today: float
    total_energy_produced_today: float
    total_cost_today: float
    current_power_draw: float
    energy_goal_progress: float
    efficiency_score: float
    active_devices_count: int
    recent_alerts: List[Dict[str, Any]]
    top_consuming_devices: List[Dict[str, Any]]


class MonthlyReport(BaseModel):
    """Monthly energy report"""
    month: str
    year: int
    total_energy_consumed: float
    total_energy_produced: float
    total_cost: float
    average_daily_consumption: float
    peak_daily_consumption: float
    energy_efficiency_score: float
    cost_savings_vs_previous_month: Optional[float] = None
    energy_savings_vs_previous_month: Optional[float] = None
    device_breakdown: Dict[str, float]
    daily_breakdown: List[DailyEnergyStats]


# Error and status schemas
class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Success response schema"""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str
    database_connected: bool
    ai_service_available: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Pagination schemas
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="desc", regex="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Base paginated response"""
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool