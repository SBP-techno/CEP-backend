import openai
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI service for energy conservation recommendations"""
    
    def __init__(self):
        self.client = None
        self.model = settings.OPENAI_MODEL
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available"""
        if settings.OPENAI_API_KEY:
            try:
                self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not configured")
            self.client = None
    
    async def check_availability(self) -> bool:
        """Check if OpenAI service is available"""
        if not self.client:
            return False
        
        try:
            # Simple test request
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI service check failed: {e}")
            return False
    
    async def get_energy_recommendations(
        self, 
        analysis_data: Dict[str, Any], 
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Get AI-powered energy conservation recommendations"""
        if not self.client:
            return self._get_fallback_recommendations(analysis_data, analysis_type)
        
        try:
            # Prepare context for AI analysis
            context = self._prepare_analysis_context(analysis_data, analysis_type)
            
            system_prompt = """You are an expert energy conservation analyst. Analyze the provided energy data and provide actionable recommendations for energy savings. 

Your response should be in JSON format with the following structure:
{
    "recommendations": ["list of specific, actionable recommendations"],
    "energy_savings_potential": "estimated kWh savings per month",
    "cost_savings_potential": "estimated cost savings per month",
    "efficiency_score": "overall efficiency score (0-100)",
    "device_specific_tips": {
        "device_name": ["specific tips for this device"]
    }
}

Focus on practical, implementable advice that can lead to measurable energy savings."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse AI response as JSON")
                return self._get_fallback_recommendations(analysis_data, analysis_type)
                
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return self._get_fallback_recommendations(analysis_data, analysis_type)
    
    async def analyze_energy_patterns(
        self, 
        energy_data: Dict[str, Any], 
        analysis_type: str
    ) -> Dict[str, Any]:
        """Analyze energy patterns and identify trends"""
        if not self.client:
            return self._get_fallback_pattern_analysis(energy_data, analysis_type)
        
        try:
            context = f"""
Energy Pattern Analysis Request:
Analysis Type: {analysis_type}
Data Period: {energy_data.get('period', {})}
Data Points: {energy_data.get('data_points', 0)}

Energy Data (sample):
{json.dumps(energy_data.get('energy_data', [])[:10], indent=2)}

Please analyze this energy data and provide insights in JSON format:
{{
    "patterns": ["list of identified patterns"],
    "anomalies": ["list of detected anomalies"],
    "trends": ["list of identified trends"],
    "insights": ["key insights from the analysis"],
    "recommendations": ["actionable recommendations based on patterns"]
}}
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert energy analyst. Analyze energy consumption patterns and provide insights in JSON format."
                    },
                    {"role": "user", "content": context}
                ],
                temperature=0.5,
                max_tokens=1200
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse pattern analysis response as JSON")
                return self._get_fallback_pattern_analysis(energy_data, analysis_type)
                
        except Exception as e:
            logger.error(f"Error analyzing energy patterns: {e}")
            return self._get_fallback_pattern_analysis(energy_data, analysis_type)
    
    async def get_device_optimization_tips(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get device-specific optimization tips"""
        if not self.client:
            return self._get_fallback_device_tips(device_data)
        
        try:
            context = f"""
Device Optimization Analysis:
Device: {device_data.get('device', {})}
Usage Stats: {device_data.get('usage_stats', {})}
Recent Data: {json.dumps(device_data.get('recent_data', [])[:5], indent=2)}

Provide optimization tips in JSON format:
{{
    "tips": ["list of specific optimization tips"],
    "potential_savings": "estimated monthly savings in kWh",
    "efficiency_score": "device efficiency score (0-100)",
    "recommendations": ["actionable recommendations"]
}}
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert in device energy optimization. Provide specific, actionable tips for improving device efficiency."
                    },
                    {"role": "user", "content": context}
                ],
                temperature=0.6,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse device tips response as JSON")
                return self._get_fallback_device_tips(device_data)
                
        except Exception as e:
            logger.error(f"Error getting device optimization tips: {e}")
            return self._get_fallback_device_tips(device_data)
    
    def _prepare_analysis_context(self, analysis_data: Dict[str, Any], analysis_type: str) -> str:
        """Prepare context for AI analysis"""
        user = analysis_data.get("user", {})
        devices = analysis_data.get("devices", [])
        energy_stats = analysis_data.get("energy_stats", {})
        
        context = f"""
Energy Conservation Analysis Request:
Analysis Type: {analysis_type}

User Profile:
- Energy Goal: {user.get('energy_goal_kwh', 'Not set')} kWh/month
- Preferred Energy Source: {user.get('preferred_energy_source', 'Mixed')}
- Number of Devices: {user.get('device_count', 0)}

Energy Statistics (Last 30 Days):
- Total Energy Consumed: {energy_stats.get('total_consumed', 0):.2f} kWh
- Total Energy Produced: {energy_stats.get('total_produced', 0):.2f} kWh
- Total Cost: ${energy_stats.get('total_cost', 0):.2f}
- Average Power Consumption: {energy_stats.get('average_power', 0):.1f} W
- Peak Power Consumption: {energy_stats.get('peak_power', 0):.1f} W

Devices:
{json.dumps(devices, indent=2)}

Recent Data Points: {analysis_data.get('recent_data_points', 0)}

Please provide comprehensive energy conservation recommendations based on this data.
"""
        return context
    
    def _get_fallback_recommendations(self, analysis_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Provide fallback recommendations when AI is not available"""
        user = analysis_data.get("user", {})
        devices = analysis_data.get("devices", [])
        energy_stats = analysis_data.get("energy_stats", {})
        
        recommendations = [
            "Set your thermostat to 68°F in winter and 78°F in summer for optimal energy efficiency",
            "Replace traditional light bulbs with LED bulbs to reduce lighting energy consumption by up to 80%",
            "Unplug devices when not in use to eliminate phantom energy consumption",
            "Use power strips to easily turn off multiple devices at once",
            "Consider installing a smart thermostat for better temperature control"
        ]
        
        # Add device-specific recommendations
        device_tips = {}
        for device in devices:
            device_name = device.get("name", "Unknown Device")
            device_type = device.get("type", "unknown")
            
            if device_type == "hvac":
                device_tips[device_name] = [
                    "Clean or replace air filters monthly",
                    "Schedule regular HVAC maintenance",
                    "Consider upgrading to a more efficient model if over 10 years old"
                ]
            elif device_type == "lighting":
                device_tips[device_name] = [
                    "Use motion sensors for automatic control",
                    "Install dimmer switches for flexible lighting",
                    "Consider smart lighting controls"
                ]
            elif device_type == "appliance":
                device_tips[device_name] = [
                    "Run full loads only",
                    "Use energy-saving modes when available",
                    "Clean regularly for optimal performance"
                ]
        
        return {
            "recommendations": recommendations,
            "energy_savings_potential": "15-25%",
            "cost_savings_potential": "$50-100 per month",
            "efficiency_score": 75,
            "device_specific_tips": device_tips
        }
    
    def _get_fallback_pattern_analysis(self, energy_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Provide fallback pattern analysis when AI is not available"""
        return {
            "patterns": [
                "Energy consumption typically peaks during evening hours",
                "Weekend usage patterns differ from weekday patterns",
                "Seasonal variations in energy consumption are evident"
            ],
            "anomalies": [
                "Unusual spike in energy consumption detected",
                "Extended periods of zero consumption may indicate sensor issues"
            ],
            "trends": [
                "Gradual increase in energy efficiency over time",
                "Consistent reduction in peak power consumption"
            ],
            "insights": [
                "Your energy usage follows typical residential patterns",
                "Consider implementing time-of-use optimization strategies"
            ],
            "recommendations": [
                "Monitor energy consumption during peak hours",
                "Implement automated controls for better efficiency",
                "Consider renewable energy sources for production"
            ]
        }
    
    def _get_fallback_device_tips(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback device optimization tips when AI is not available"""
        device = device_data.get("device", {})
        device_type = device.get("type", "unknown")
        
        tips = [
            "Ensure proper maintenance and cleaning",
            "Check for energy-efficient settings",
            "Consider upgrading to newer, more efficient models"
        ]
        
        if device_type == "hvac":
            tips.extend([
                "Clean or replace air filters regularly",
                "Schedule professional maintenance annually",
                "Use programmable thermostats for better control"
            ])
        elif device_type == "lighting":
            tips.extend([
                "Switch to LED bulbs for better efficiency",
                "Use natural lighting when possible",
                "Install motion sensors for automatic control"
            ])
        elif device_type == "appliance":
            tips.extend([
                "Run full loads only",
                "Use energy-saving modes",
                "Unplug when not in use"
            ])
        
        return {
            "tips": tips,
            "potential_savings": "10-20%",
            "efficiency_score": 80,
            "recommendations": [
                "Regular maintenance is key to optimal performance",
                "Consider smart controls for better automation",
                "Monitor usage patterns for optimization opportunities"
            ]
        }


# Global instance
openai_service = OpenAIService()