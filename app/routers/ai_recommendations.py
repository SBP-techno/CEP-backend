from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import logging

from app.database import get_database
from app.services.openai_service import OpenAIService
from app.schemas.energy import (
    AIRecommendationRequest, AIRecommendationResponse,
    EnergyAnalysisRequest, EnergyAnalysisResponse,
    EnergyComparisonRequest, EnergyComparisonResponse,
    DeviceEfficiencyReport, UserEfficiencyReport,
    SuccessResponse, ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Helper functions
def get_db():
    """Get database instance"""
    return get_database()


async def get_user_by_id(user_id: str, db) -> Optional[dict]:
    """Get user by ID"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


async def get_device_by_id(device_id: str, db) -> Optional[dict]:
    """Get device by ID"""
    try:
        device = await db.devices.find_one({"_id": ObjectId(device_id)})
        return device
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return None


# AI Service endpoints
@router.get("/ai-status")
async def check_ai_service_status():
    """Check if AI service is available"""
    try:
        openai_service = OpenAIService()
        is_available = await openai_service.check_availability()
        
        return {
            "status": "available" if is_available else "unavailable",
            "service": "OpenAI",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking AI service status: {e}")
        return {
            "status": "error",
            "service": "OpenAI",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/users/{user_id}/recommendations", response_model=AIRecommendationResponse)
async def get_ai_recommendations(
    user_id: str,
    request: AIRecommendationRequest,
    db=Depends(get_db)
):
    """Get AI-powered energy conservation recommendations for a user"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's energy data and devices
        devices = await db.devices.find({"user_id": user_id}).to_list(length=None)
        
        # Get recent energy data (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        energy_data = await db.energy_data.find({
            "user_id": user_id,
            "timestamp": {"$gte": thirty_days_ago}
        }).sort("timestamp", -1).to_list(length=100)
        
        # Get energy statistics
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                    "total_energy_produced": {"$sum": "$energy_production_kwh"},
                    "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                    "average_power_consumption": {"$avg": "$power_consumption_watts"},
                    "peak_power_consumption": {"$max": "$power_consumption_watts"}
                }
            }
        ]
        
        stats_result = list(await db.energy_data.aggregate(pipeline))
        stats = stats_result[0] if stats_result else {
            "total_energy_consumed": 0,
            "total_energy_produced": 0,
            "total_cost": 0,
            "average_power_consumption": 0,
            "peak_power_consumption": 0
        }
        
        # Prepare data for AI analysis
        analysis_data = {
            "user": {
                "energy_goal_kwh": user.get("energy_goal_kwh", 1000),
                "preferred_energy_source": user.get("preferred_energy_source", "mixed"),
                "device_count": len(devices)
            },
            "devices": [
                {
                    "name": device["name"],
                    "type": device["device_type"],
                    "power_rating": device.get("power_rating_watts", 0),
                    "total_consumed": device.get("total_energy_consumed", 0),
                    "is_smart": device.get("is_smart_device", False)
                }
                for device in devices
            ],
            "energy_stats": {
                "total_consumed": stats["total_energy_consumed"],
                "total_produced": stats["total_energy_produced"],
                "total_cost": stats["total_cost"],
                "average_power": stats["average_power_consumption"],
                "peak_power": stats["peak_power_consumption"]
            },
            "recent_data_points": len(energy_data)
        }
        
        # Get AI recommendations
        openai_service = OpenAIService()
        recommendations = await openai_service.get_energy_recommendations(
            analysis_data, request.analysis_type
        )
        
        return AIRecommendationResponse(
            user_id=user_id,
            analysis_type=request.analysis_type,
            recommendations=recommendations.get("recommendations", []),
            energy_savings_potential=recommendations.get("energy_savings_potential"),
            cost_savings_potential=recommendations.get("cost_savings_potential"),
            efficiency_score=recommendations.get("efficiency_score"),
            device_specific_tips=recommendations.get("device_specific_tips")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{user_id}/energy-analysis", response_model=EnergyAnalysisResponse)
async def analyze_energy_patterns(
    user_id: str,
    request: EnergyAnalysisRequest,
    db=Depends(get_db)
):
    """Analyze energy patterns and identify trends"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get energy data for the specified period
        energy_data = await db.energy_data.find({
            "user_id": user_id,
            "timestamp": {"$gte": request.start_date, "$lte": request.end_date}
        }).sort("timestamp", 1).to_list(length=None)
        
        if not energy_data:
            raise HTTPException(status_code=404, detail="No energy data found for the specified period")
        
        # Prepare data for analysis
        analysis_data = {
            "period": {
                "start": request.start_date.isoformat(),
                "end": request.end_date.isoformat()
            },
            "data_points": len(energy_data),
            "energy_data": [
                {
                    "timestamp": data["timestamp"].isoformat(),
                    "consumption": data["energy_consumption_kwh"],
                    "production": data["energy_production_kwh"],
                    "power": data["power_consumption_watts"],
                    "cost": data.get("total_cost", 0),
                    "device_id": data["device_id"]
                }
                for data in energy_data
            ]
        }
        
        # Get AI analysis
        openai_service = OpenAIService()
        analysis_result = await openai_service.analyze_energy_patterns(
            analysis_data, request.analysis_type
        )
        
        return EnergyAnalysisResponse(
            user_id=user_id,
            analysis_type=request.analysis_type,
            patterns_found=analysis_result.get("patterns", []),
            anomalies_detected=analysis_result.get("anomalies", []),
            trends_identified=analysis_result.get("trends", []),
            insights=analysis_result.get("insights", []),
            recommendations=analysis_result.get("recommendations", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing energy patterns for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/devices/{device_id}/optimization-tips", response_model=Dict[str, Any])
async def get_device_optimization_tips(
    device_id: str,
    db=Depends(get_db)
):
    """Get device-specific optimization tips"""
    try:
        device = await get_device_by_id(device_id, db)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get device's energy data (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        energy_data = await db.energy_data.find({
            "device_id": device_id,
            "timestamp": {"$gte": thirty_days_ago}
        }).sort("timestamp", -1).to_list(length=50)
        
        # Get device statistics
        pipeline = [
            {
                "$match": {
                    "device_id": device_id,
                    "timestamp": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                    "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                    "average_power": {"$avg": "$power_consumption_watts"},
                    "peak_power": {"$max": "$power_consumption_watts"},
                    "usage_hours": {"$sum": 1}
                }
            }
        ]
        
        stats_result = list(await db.energy_data.aggregate(pipeline))
        stats = stats_result[0] if stats_result else {
            "total_energy_consumed": 0,
            "total_cost": 0,
            "average_power": 0,
            "peak_power": 0,
            "usage_hours": 0
        }
        
        # Prepare device data for analysis
        device_data = {
            "device": {
                "name": device["name"],
                "type": device["device_type"],
                "manufacturer": device.get("manufacturer", ""),
                "model": device.get("model", ""),
                "power_rating": device.get("power_rating_watts", 0),
                "is_smart": device.get("is_smart_device", False),
                "location": device.get("location", "")
            },
            "usage_stats": {
                "total_energy_consumed": stats["total_energy_consumed"],
                "total_cost": stats["total_cost"],
                "average_power": stats["average_power"],
                "peak_power": stats["peak_power"],
                "usage_hours": stats["usage_hours"]
            },
            "recent_data": [
                {
                    "timestamp": data["timestamp"].isoformat(),
                    "consumption": data["energy_consumption_kwh"],
                    "power": data["power_consumption_watts"],
                    "cost": data.get("total_cost", 0)
                }
                for data in energy_data[:10]  # Last 10 readings
            ]
        }
        
        # Get AI optimization tips
        openai_service = OpenAIService()
        optimization_tips = await openai_service.get_device_optimization_tips(device_data)
        
        return {
            "device_id": device_id,
            "device_name": device["name"],
            "device_type": device["device_type"],
            "optimization_tips": optimization_tips.get("tips", []),
            "potential_savings": optimization_tips.get("potential_savings"),
            "efficiency_score": optimization_tips.get("efficiency_score"),
            "recommendations": optimization_tips.get("recommendations", []),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization tips for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{user_id}/compare-usage", response_model=EnergyComparisonResponse)
async def compare_energy_usage(
    user_id: str,
    request: EnergyComparisonRequest,
    db=Depends(get_db)
):
    """Compare energy usage between two periods"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get current period data
        current_pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": request.start_date, "$lte": request.end_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                    "total_energy_produced": {"$sum": "$energy_production_kwh"},
                    "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                    "average_power_consumption": {"$avg": "$power_consumption_watts"},
                    "peak_power_consumption": {"$max": "$power_consumption_watts"},
                    "data_points_count": {"$sum": 1}
                }
            }
        ]
        
        current_result = list(await db.energy_data.aggregate(current_pipeline))
        current_stats = current_result[0] if current_result else {
            "total_energy_consumed": 0,
            "total_energy_produced": 0,
            "total_cost": 0,
            "average_power_consumption": 0,
            "peak_power_consumption": 0,
            "data_points_count": 0
        }
        
        current_period = {
            "total_energy_consumed": current_stats["total_energy_consumed"],
            "total_energy_produced": current_stats["total_energy_produced"],
            "total_cost": current_stats["total_cost"],
            "average_power_consumption": current_stats["average_power_consumption"],
            "peak_power_consumption": current_stats["peak_power_consumption"],
            "period_start": request.start_date,
            "period_end": request.end_date,
            "data_points_count": current_stats["data_points_count"]
        }
        
        comparison_period = None
        percentage_change = None
        cost_savings = None
        energy_savings = None
        
        # Get comparison period data if provided
        if request.comparison_start_date and request.comparison_end_date:
            comparison_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": request.comparison_start_date, "$lte": request.comparison_end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                        "total_energy_produced": {"$sum": "$energy_production_kwh"},
                        "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                        "average_power_consumption": {"$avg": "$power_consumption_watts"},
                        "peak_power_consumption": {"$max": "$power_consumption_watts"},
                        "data_points_count": {"$sum": 1}
                    }
                }
            ]
            
            comparison_result = list(await db.energy_data.aggregate(comparison_pipeline))
            comparison_stats = comparison_result[0] if comparison_result else {
                "total_energy_consumed": 0,
                "total_energy_produced": 0,
                "total_cost": 0,
                "average_power_consumption": 0,
                "peak_power_consumption": 0,
                "data_points_count": 0
            }
            
            comparison_period = {
                "total_energy_consumed": comparison_stats["total_energy_consumed"],
                "total_energy_produced": comparison_stats["total_energy_produced"],
                "total_cost": comparison_stats["total_cost"],
                "average_power_consumption": comparison_stats["average_power_consumption"],
                "peak_power_consumption": comparison_stats["peak_power_consumption"],
                "period_start": request.comparison_start_date,
                "period_end": request.comparison_end_date,
                "data_points_count": comparison_stats["data_points_count"]
            }
            
            # Calculate changes
            if comparison_stats["total_energy_consumed"] > 0:
                percentage_change = ((current_stats["total_energy_consumed"] - comparison_stats["total_energy_consumed"]) / comparison_stats["total_energy_consumed"]) * 100
                energy_savings = comparison_stats["total_energy_consumed"] - current_stats["total_energy_consumed"]
                cost_savings = comparison_stats["total_cost"] - current_stats["total_cost"]
        
        return EnergyComparisonResponse(
            current_period=current_period,
            comparison_period=comparison_period,
            percentage_change=percentage_change,
            cost_savings=cost_savings,
            energy_savings=energy_savings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing energy usage for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}/efficiency-report", response_model=UserEfficiencyReport)
async def get_user_efficiency_report(
    user_id: str,
    db=Depends(get_db)
):
    """Get comprehensive efficiency report for a user"""
    try:
        user = await get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's devices
        devices = await db.devices.find({"user_id": user_id}).to_list(length=None)
        
        # Get energy data for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get overall user statistics
        user_pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                    "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}}
                }
            }
        ]
        
        user_stats_result = list(await db.energy_data.aggregate(user_pipeline))
        user_stats = user_stats_result[0] if user_stats_result else {
            "total_energy_consumed": 0,
            "total_cost": 0
        }
        
        # Get device-specific reports
        device_reports = []
        total_potential_savings = 0
        
        for device in devices:
            device_pipeline = [
                {
                    "$match": {
                        "device_id": str(device["_id"]),
                        "timestamp": {"$gte": thirty_days_ago}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_energy_consumed": {"$sum": "$energy_consumption_kwh"},
                        "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                        "average_power": {"$avg": "$power_consumption_watts"}
                    }
                }
            ]
            
            device_stats_result = list(await db.energy_data.aggregate(device_pipeline))
            device_stats = device_stats_result[0] if device_stats_result else {
                "total_energy_consumed": 0,
                "total_cost": 0,
                "average_power": 0
            }
            
            # Calculate efficiency score (simplified)
            power_rating = device.get("power_rating_watts", 0)
            efficiency_score = 0
            if power_rating > 0:
                efficiency_score = min(100, max(0, (power_rating - device_stats["average_power"]) / power_rating * 100))
            
            # Get device-specific recommendations
            openai_service = OpenAIService()
            device_data = {
                "device": {
                    "name": device["name"],
                    "type": device["device_type"],
                    "power_rating": power_rating
                },
                "usage": {
                    "energy_consumed": device_stats["total_energy_consumed"],
                    "cost": device_stats["total_cost"],
                    "average_power": device_stats["average_power"]
                }
            }
            
            device_tips = await openai_service.get_device_optimization_tips(device_data)
            recommendations = device_tips.get("recommendations", [])
            potential_savings = device_tips.get("potential_savings", 0)
            total_potential_savings += potential_savings
            
            device_reports.append(DeviceEfficiencyReport(
                device_id=str(device["_id"]),
                device_name=device["name"],
                device_type=device["device_type"],
                efficiency_score=efficiency_score,
                energy_consumption=device_stats["total_energy_consumed"],
                cost=device_stats["total_cost"],
                recommendations=recommendations,
                potential_savings=potential_savings
            ))
        
        # Calculate overall efficiency score
        overall_efficiency_score = sum(report.efficiency_score for report in device_reports) / len(device_reports) if device_reports else 0
        
        # Get general recommendations
        openai_service = OpenAIService()
        general_recommendations = await openai_service.get_energy_recommendations({
            "user": user,
            "devices": [{"name": d["name"], "type": d["device_type"]} for d in devices],
            "energy_stats": user_stats
        }, "general")
        
        return UserEfficiencyReport(
            user_id=user_id,
            overall_efficiency_score=overall_efficiency_score,
            total_energy_consumed=user_stats["total_energy_consumed"],
            total_cost=user_stats["total_cost"],
            device_reports=device_reports,
            recommendations=general_recommendations.get("recommendations", []),
            potential_monthly_savings=total_potential_savings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting efficiency report for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")