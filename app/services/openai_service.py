from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
import logging

from app.config import settings
from app.schemas.energy import EnergyData, Device, EnergyStats

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API integration"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def get_energy_recommendations(
        self,
        user_data: Dict[str, Any],
        energy_stats: EnergyStats,
        devices: List[Device],
        recent_energy_data: List[EnergyData]
    ) -> Dict[str, Any]:
        """Generate personalized energy conservation recommendations"""
        
        if not self.client:
            return {"error": "OpenAI service not configured"}
        
        try:
            # Prepare context for the AI
            context = self._prepare_energy_context(user_data, energy_stats, devices, recent_energy_data)
            
            system_prompt = """You are an expert energy conservation advisor. Analyze the user's energy consumption data and provide personalized recommendations to reduce energy usage and costs. 

            Provide your response in JSON format with the following structure:
            {
                "overall_assessment": "Brief assessment of current energy usage",
                "recommendations": [
                    {
                        "category": "heating/cooling/lighting/appliances/general",
                        "title": "Recommendation title",
                        "description": "Detailed description",
                        "potential_savings_kwh": estimated_monthly_savings_in_kwh,
                        "potential_savings_usd": estimated_monthly_savings_in_dollars,
                        "difficulty": "easy/medium/hard",
                        "priority": "high/medium/low"
                    }
                ],
                "insights": [
                    "Key insight about energy usage patterns",
                    "Another insight"
                ],
                "goals": {
                    "recommended_monthly_target_kwh": number,
                    "timeframe_to_achieve": "timeframe description"
                }
            }"""
            
            user_prompt = f"""Analyze this user's energy data and provide recommendations:

            {context}
            
            Focus on practical, actionable advice that can realistically reduce energy consumption."""
            
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            recommendations = json.loads(content)
            
            return recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            return {"error": "Failed to parse AI response"}
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"error": f"AI service error: {str(e)}"}
    
    async def analyze_energy_patterns(
        self,
        energy_data: List[EnergyData],
        time_period: str = "week"
    ) -> Dict[str, Any]:
        """Analyze energy consumption patterns"""
        
        if not self.client:
            return {"error": "OpenAI service not configured"}
        
        try:
            # Prepare data for analysis
            data_summary = self._prepare_pattern_analysis_data(energy_data, time_period)
            
            system_prompt = """You are an energy analyst. Analyze the energy consumption patterns and identify trends, anomalies, and insights.

            Provide your response in JSON format:
            {
                "patterns": [
                    {
                        "type": "trend/anomaly/seasonal/daily",
                        "description": "Description of the pattern",
                        "significance": "high/medium/low"
                    }
                ],
                "peak_usage_times": ["time periods when usage is highest"],
                "efficiency_score": score_out_of_100,
                "trends": {
                    "consumption_trend": "increasing/decreasing/stable",
                    "trend_percentage": percentage_change,
                    "prediction": "Short prediction for next period"
                }
            }"""
            
            user_prompt = f"Analyze these energy consumption patterns:\n\n{data_summary}"
            
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return {"error": f"Pattern analysis failed: {str(e)}"}
    
    async def get_device_optimization_tips(
        self,
        device: Device,
        device_energy_data: List[EnergyData]
    ) -> Dict[str, Any]:
        """Get device-specific optimization recommendations"""
        
        if not self.client:
            return {"error": "OpenAI service not configured"}
        
        try:
            device_context = self._prepare_device_context(device, device_energy_data)
            
            system_prompt = f"""You are an expert on {device.device_type.value} energy optimization. Provide specific recommendations for this device.

            Respond in JSON format:
            {{
                "device_assessment": "Current performance assessment",
                "optimization_tips": [
                    {{
                        "tip": "Specific optimization tip",
                        "impact": "high/medium/low",
                        "ease_of_implementation": "easy/medium/hard"
                    }}
                ],
                "maintenance_reminders": ["maintenance task 1", "maintenance task 2"],
                "replacement_consideration": {{
                    "should_consider": true/false,
                    "reason": "reason if true"
                }}
            }}"""
            
            user_prompt = f"Analyze this device and provide optimization recommendations:\n\n{device_context}"
            
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            tips = json.loads(content)
            
            return tips
            
        except Exception as e:
            logger.error(f"Device optimization error: {e}")
            return {"error": f"Device optimization failed: {str(e)}"}
    
    def _prepare_energy_context(
        self,
        user_data: Dict[str, Any],
        energy_stats: EnergyStats,
        devices: List[Device],
        recent_energy_data: List[EnergyData]
    ) -> str:
        """Prepare context for energy recommendations"""
        
        context = f"""
        USER PROFILE:
        - Energy Goal: {user_data.get('energy_goal_kwh', 'Not set')} kWh/month
        - Preferred Temperature: {user_data.get('preferred_temperature', 'Not set')}°C
        
        CURRENT ENERGY STATISTICS:
        - Total Consumption: {energy_stats.total_consumption_kwh:.2f} kWh
        - Total Cost: ${energy_stats.total_cost_usd:.2f}
        - Average Power: {energy_stats.average_power_watts or 'N/A'} W
        - Peak Power: {energy_stats.peak_power_watts or 'N/A'} W
        - Period: {energy_stats.period_start} to {energy_stats.period_end}
        
        DEVICES ({len(devices)} total):
        """
        
        for device in devices:
            context += f"""
        - {device.name} ({device.device_type.value})
          Location: {device.location or 'Not specified'}
          Rated Power: {device.rated_power_watts or 'Unknown'} W
          Smart Device: {'Yes' if device.is_smart_device else 'No'}
        """
        
        if recent_energy_data:
            context += f"\nRECENT ENERGY DATA (last {len(recent_energy_data)} readings):\n"
            for data in recent_energy_data[-5:]:  # Last 5 readings
                context += f"- {data.timestamp}: {data.consumption_kwh:.2f} kWh, {data.power_watts or 'N/A'} W\n"
        
        return context
    
    def _prepare_pattern_analysis_data(
        self,
        energy_data: List[EnergyData],
        time_period: str
    ) -> str:
        """Prepare data for pattern analysis"""
        
        if not energy_data:
            return "No energy data available for analysis."
        
        # Sort data by timestamp
        sorted_data = sorted(energy_data, key=lambda x: x.timestamp)
        
        summary = f"Energy consumption data for {time_period} analysis ({len(sorted_data)} data points):\n\n"
        
        # Group by day for daily patterns
        daily_data = {}
        for data in sorted_data:
            date_key = data.timestamp.date()
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(data)
        
        summary += "Daily consumption summary:\n"
        for date, day_data in sorted(daily_data.items()):
            total_consumption = sum(d.consumption_kwh for d in day_data)
            avg_power = sum(d.power_watts for d in day_data if d.power_watts) / len([d for d in day_data if d.power_watts]) if any(d.power_watts for d in day_data) else 0
            summary += f"- {date}: {total_consumption:.2f} kWh, Avg Power: {avg_power:.1f} W\n"
        
        return summary
    
    def _prepare_device_context(
        self,
        device: Device,
        device_energy_data: List[EnergyData]
    ) -> str:
        """Prepare context for device optimization"""
        
        context = f"""
        DEVICE INFORMATION:
        - Name: {device.name}
        - Type: {device.device_type.value}
        - Model: {device.model or 'Unknown'}
        - Manufacturer: {device.manufacturer or 'Unknown'}
        - Location: {device.location or 'Not specified'}
        - Rated Power: {device.rated_power_watts or 'Unknown'} W
        - Smart Device: {'Yes' if device.is_smart_device else 'No'}
        - Last Seen: {device.last_seen or 'Unknown'}
        
        RECENT ENERGY DATA:
        """
        
        if device_energy_data:
            sorted_data = sorted(device_energy_data, key=lambda x: x.timestamp)
            for data in sorted_data[-10:]:  # Last 10 readings
                context += f"- {data.timestamp}: {data.consumption_kwh:.3f} kWh, {data.power_watts or 'N/A'} W"
                if data.temperature_celsius:
                    context += f", Temp: {data.temperature_celsius:.1f}°C"
                context += "\n"
        else:
            context += "No recent energy data available for this device.\n"
        
        return context


# Global instance
openai_service = OpenAIService()