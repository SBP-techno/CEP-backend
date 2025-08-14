#!/usr/bin/env python3
"""
Simple test script for the Energy Conservation API
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

async def test_api():
    """Test the API endpoints"""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Energy Conservation API...\n")
        
        # Test 1: Health check
        print("1. Testing health check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   ✅ Health check: {response.status_code}")
            print(f"   📊 Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return
        
        # Test 2: Create a user
        print("\n2. Testing user creation...")
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "energy_goal_kwh": 800.0,
            "preferred_energy_source": "mixed"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/energy/users/", json=user_data)
            if response.status_code == 200:
                user = response.json()
                user_id = user["id"]
                print(f"   ✅ User created: {user['username']}")
                print(f"   🆔 User ID: {user_id}")
            else:
                print(f"   ❌ User creation failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                return
        except Exception as e:
            print(f"   ❌ User creation failed: {e}")
            return
        
        # Test 3: Create a device
        print("\n3. Testing device creation...")
        device_data = {
            "name": "Living Room AC",
            "device_type": "hvac",
            "location": "Living Room",
            "manufacturer": "Test Corp",
            "model": "AC-2024",
            "power_rating_watts": 1500.0,
            "is_smart_device": True
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/energy/users/{user_id}/devices/", json=device_data)
            if response.status_code == 200:
                device = response.json()
                device_id = device["id"]
                print(f"   ✅ Device created: {device['name']}")
                print(f"   🆔 Device ID: {device_id}")
            else:
                print(f"   ❌ Device creation failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                return
        except Exception as e:
            print(f"   ❌ Device creation failed: {e}")
            return
        
        # Test 4: Add energy data
        print("\n4. Testing energy data creation...")
        energy_data = {
            "power_consumption_watts": 1200.0,
            "energy_consumption_kwh": 2.4,
            "energy_production_kwh": 0.0,
            "voltage": 120.0,
            "current": 10.0,
            "temperature": 22.5,
            "humidity": 45.0,
            "cost_per_kwh": 0.12,
            "total_cost": 0.288,
            "data_source": "manual"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/energy/devices/{device_id}/energy-data/", json=energy_data)
            if response.status_code == 200:
                energy = response.json()
                print(f"   ✅ Energy data created: {energy['energy_consumption_kwh']} kWh")
                print(f"   💰 Cost: ${energy['total_cost']}")
            else:
                print(f"   ❌ Energy data creation failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Energy data creation failed: {e}")
        
        # Test 5: Get user statistics
        print("\n5. Testing energy statistics...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/energy/users/{user_id}/energy-stats/")
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✅ Energy stats retrieved")
                print(f"   📊 Total consumed: {stats['total_energy_consumed']} kWh")
                print(f"   💰 Total cost: ${stats['total_cost']}")
            else:
                print(f"   ❌ Energy stats failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Energy stats failed: {e}")
        
        # Test 6: Test AI recommendations (if available)
        print("\n6. Testing AI recommendations...")
        ai_request = {
            "analysis_type": "general",
            "include_cost_analysis": True,
            "include_efficiency_tips": True
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/ai/users/{user_id}/recommendations", json=ai_request)
            if response.status_code == 200:
                ai_response = response.json()
                print(f"   ✅ AI recommendations retrieved")
                print(f"   🤖 Recommendations count: {len(ai_response.get('recommendations', []))}")
                if ai_response.get('recommendations'):
                    print(f"   💡 First recommendation: {ai_response['recommendations'][0]}")
            else:
                print(f"   ⚠️  AI recommendations failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
        except Exception as e:
            print(f"   ⚠️  AI recommendations failed: {e}")
        
        # Test 7: Get user with devices
        print("\n7. Testing user with devices...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/energy/users/{user_id}")
            if response.status_code == 200:
                user_with_devices = response.json()
                print(f"   ✅ User with devices retrieved")
                print(f"   👤 User: {user_with_devices['username']}")
                print(f"   📱 Devices count: {len(user_with_devices.get('devices', []))}")
            else:
                print(f"   ❌ User retrieval failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ User retrieval failed: {e}")
        
        print("\n🎉 API testing completed!")
        print(f"📖 API Documentation: {BASE_URL}/docs")

if __name__ == "__main__":
    asyncio.run(test_api())