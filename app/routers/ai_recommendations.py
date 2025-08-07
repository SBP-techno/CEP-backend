from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models.users import User
from app.models.devices import Device
from app.models.energy_data import EnergyData
from app.schemas.energy import EnergyStats
from app.services.openai_service import openai_service

router = APIRouter()


@router.post("/users/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI-powered energy conservation recommendations for a user"""
    
    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user data
    user_data = {
        "energy_goal_kwh": user.energy_goal_kwh,
        "preferred_temperature": user.preferred_temperature,
        "username": user.username,
        "full_name": user.full_name
    }
    
    # Get energy statistics for the period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get aggregated energy stats
    from sqlalchemy import func
    result = await db.execute(
        select(
            func.sum(EnergyData.consumption_kwh).label("total_consumption"),
            func.sum(EnergyData.production_kwh).label("total_production"),
            func.sum(EnergyData.cost_usd).label("total_cost"),
            func.avg(EnergyData.power_watts).label("avg_power"),
            func.max(EnergyData.power_watts).label("peak_power"),
            func.count(func.distinct(EnergyData.device_id)).label("device_count")
        ).where(
            and_(
                EnergyData.user_id == user_id,
                EnergyData.timestamp >= start_date,
                EnergyData.timestamp <= end_date
            )
        )
    )
    
    stats = result.first()
    energy_stats = EnergyStats(
        total_consumption_kwh=stats.total_consumption or 0.0,
        total_production_kwh=stats.total_production or 0.0,
        total_cost_usd=stats.total_cost or 0.0,
        average_power_watts=stats.avg_power,
        peak_power_watts=stats.peak_power,
        period_start=start_date,
        period_end=end_date,
        device_count=stats.device_count or 0
    )
    
    # Get user devices
    result = await db.execute(
        select(Device).where(Device.user_id == user_id, Device.is_active == True)
    )
    devices = result.scalars().all()
    
    # Get recent energy data
    result = await db.execute(
        select(EnergyData)
        .where(
            and_(
                EnergyData.user_id == user_id,
                EnergyData.timestamp >= start_date
            )
        )
        .order_by(desc(EnergyData.timestamp))
        .limit(100)
    )
    recent_energy_data = result.scalars().all()
    
    # Get AI recommendations
    recommendations = await openai_service.get_energy_recommendations(
        user_data=user_data,
        energy_stats=energy_stats,
        devices=devices,
        recent_energy_data=recent_energy_data
    )
    
    return {
        "user_id": user_id,
        "analysis_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "energy_stats": energy_stats.model_dump(),
        "recommendations": recommendations
    }


@router.post("/users/{user_id}/energy-analysis")
async def analyze_user_energy_patterns(
    user_id: int,
    time_period: str = Query("week", regex="^(week|month|quarter)$"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze energy consumption patterns for a user"""
    
    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Determine time range based on period
    end_date = datetime.utcnow()
    if time_period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif time_period == "month":
        start_date = end_date - timedelta(days=30)
    elif time_period == "quarter":
        start_date = end_date - timedelta(days=90)
    
    # Get energy data for the period
    result = await db.execute(
        select(EnergyData)
        .where(
            and_(
                EnergyData.user_id == user_id,
                EnergyData.timestamp >= start_date,
                EnergyData.timestamp <= end_date
            )
        )
        .order_by(EnergyData.timestamp)
    )
    energy_data = result.scalars().all()
    
    if not energy_data:
        raise HTTPException(status_code=404, detail="No energy data found for the specified period")
    
    # Get AI analysis
    analysis = await openai_service.analyze_energy_patterns(
        energy_data=energy_data,
        time_period=time_period
    )
    
    return {
        "user_id": user_id,
        "time_period": time_period,
        "analysis_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "data_points": len(energy_data),
        "analysis": analysis
    }


@router.post("/devices/{device_id}/optimization-tips")
async def get_device_optimization_tips(
    device_id: int,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI-powered optimization tips for a specific device"""
    
    # Verify device exists
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_active == True)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get device energy data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    result = await db.execute(
        select(EnergyData)
        .where(
            and_(
                EnergyData.device_id == device_id,
                EnergyData.timestamp >= start_date
            )
        )
        .order_by(EnergyData.timestamp)
    )
    device_energy_data = result.scalars().all()
    
    # Get AI optimization tips
    tips = await openai_service.get_device_optimization_tips(
        device=device,
        device_energy_data=device_energy_data
    )
    
    return {
        "device_id": device_id,
        "device_name": device.name,
        "device_type": device.device_type.value,
        "analysis_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "data_points": len(device_energy_data),
        "optimization_tips": tips
    }


@router.post("/users/{user_id}/compare-usage")
async def compare_energy_usage(
    user_id: int,
    period1_days: int = Query(30, ge=1, le=365, description="Days for first period"),
    period2_days: int = Query(30, ge=1, le=365, description="Days for second period"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Compare energy usage between two time periods with AI insights"""
    
    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from sqlalchemy import func
    
    # Calculate date ranges
    end_date = datetime.utcnow()
    period1_start = end_date - timedelta(days=period1_days)
    period2_end = period1_start
    period2_start = period2_end - timedelta(days=period2_days)
    
    # Get stats for period 1 (recent)
    result = await db.execute(
        select(
            func.sum(EnergyData.consumption_kwh).label("total_consumption"),
            func.sum(EnergyData.production_kwh).label("total_production"),
            func.sum(EnergyData.cost_usd).label("total_cost"),
            func.avg(EnergyData.power_watts).label("avg_power"),
            func.count(EnergyData.id).label("data_points")
        ).where(
            and_(
                EnergyData.user_id == user_id,
                EnergyData.timestamp >= period1_start,
                EnergyData.timestamp <= end_date
            )
        )
    )
    period1_stats = result.first()
    
    # Get stats for period 2 (older)
    result = await db.execute(
        select(
            func.sum(EnergyData.consumption_kwh).label("total_consumption"),
            func.sum(EnergyData.production_kwh).label("total_production"),
            func.sum(EnergyData.cost_usd).label("total_cost"),
            func.avg(EnergyData.power_watts).label("avg_power"),
            func.count(EnergyData.id).label("data_points")
        ).where(
            and_(
                EnergyData.user_id == user_id,
                EnergyData.timestamp >= period2_start,
                EnergyData.timestamp <= period2_end
            )
        )
    )
    period2_stats = result.first()
    
    # Calculate percentage changes
    def calculate_change(new_val, old_val):
        if old_val and old_val != 0:
            return ((new_val or 0) - old_val) / old_val * 100
        return 0
    
    consumption_change = calculate_change(
        period1_stats.total_consumption, 
        period2_stats.total_consumption
    )
    cost_change = calculate_change(
        period1_stats.total_cost, 
        period2_stats.total_cost
    )
    power_change = calculate_change(
        period1_stats.avg_power, 
        period2_stats.avg_power
    )
    
    # Prepare comparison data for AI analysis
    comparison_context = f"""
    Energy Usage Comparison:
    
    Recent Period ({period1_days} days):
    - Consumption: {period1_stats.total_consumption or 0:.2f} kWh
    - Cost: ${period1_stats.total_cost or 0:.2f}
    - Average Power: {period1_stats.avg_power or 0:.1f} W
    
    Previous Period ({period2_days} days):
    - Consumption: {period2_stats.total_consumption or 0:.2f} kWh
    - Cost: ${period2_stats.total_cost or 0:.2f}
    - Average Power: {period2_stats.avg_power or 0:.1f} W
    
    Changes:
    - Consumption: {consumption_change:+.1f}%
    - Cost: {cost_change:+.1f}%
    - Average Power: {power_change:+.1f}%
    """
    
    # Get AI insights on the comparison
    try:
        if openai_service.client:
            response = await openai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an energy analyst. Analyze the energy usage comparison and provide insights in JSON format with 'interpretation', 'trends', and 'recommendations' fields."
                    },
                    {
                        "role": "user", 
                        "content": f"Analyze this energy usage comparison and provide insights:\n\n{comparison_context}"
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            import json
            ai_insights = json.loads(response.choices[0].message.content)
        else:
            ai_insights = {"error": "AI service not configured"}
    except Exception as e:
        ai_insights = {"error": f"AI analysis failed: {str(e)}"}
    
    return {
        "user_id": user_id,
        "comparison": {
            "recent_period": {
                "start_date": period1_start.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period1_days,
                "consumption_kwh": period1_stats.total_consumption or 0.0,
                "cost_usd": period1_stats.total_cost or 0.0,
                "avg_power_watts": period1_stats.avg_power or 0.0,
                "data_points": period1_stats.data_points or 0
            },
            "previous_period": {
                "start_date": period2_start.isoformat(),
                "end_date": period2_end.isoformat(),
                "days": period2_days,
                "consumption_kwh": period2_stats.total_consumption or 0.0,
                "cost_usd": period2_stats.total_cost or 0.0,
                "avg_power_watts": period2_stats.avg_power or 0.0,
                "data_points": period2_stats.data_points or 0
            },
            "changes": {
                "consumption_change_percent": round(consumption_change, 2),
                "cost_change_percent": round(cost_change, 2),
                "power_change_percent": round(power_change, 2)
            }
        },
        "ai_insights": ai_insights
    }


@router.get("/ai-status")
async def get_ai_service_status() -> Dict[str, Any]:
    """Get the status of the AI service"""
    
    is_configured = openai_service.client is not None
    
    return {
        "ai_service_configured": is_configured,
        "openai_model": "gpt-3.5-turbo" if is_configured else None,
        "status": "ready" if is_configured else "not_configured",
        "message": "AI service is ready" if is_configured else "OpenAI API key not configured"
    }