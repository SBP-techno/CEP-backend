#!/usr/bin/env python3
"""
Comprehensive API and Database Connection Test
Tests both API functionality and database connectivity with proper error handling
"""

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add the current directory to Python path
sys.path.insert(0, '/workspace')

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class APITester:
    def __init__(self):
        self.results = {
            "database_connection": {"status": "unknown", "details": ""},
            "api_health": {"status": "unknown", "details": ""},
            "api_endpoints": {"status": "unknown", "details": ""},
            "error_handling": {"status": "unknown", "details": ""},
            "overall_status": "unknown"
        }
        self.test_data = {}

    async def test_database_connection(self):
        """Test database connection directly"""
        print("🔍 Testing Database Connection...")
        try:
            from app.database import connect_to_mongo, get_client
            await connect_to_mongo()
            client = get_client()
            if client:
                await client.admin.command('ping')
                self.results["database_connection"] = {
                    "status": "success",
                    "details": "MongoDB connection established successfully"
                }
                print("   ✅ Database connection successful")
                return True
            else:
                self.results["database_connection"] = {
                    "status": "failed",
                    "details": "MongoDB client not available"
                }
                print("   ❌ Database client not available")
                return False
        except Exception as e:
            self.results["database_connection"] = {
                "status": "failed",
                "details": f"MongoDB connection failed: {str(e)}"
            }
            print(f"   ❌ Database connection failed: {str(e)}")
            return False

    async def test_api_server_running(self):
        """Test if API server is running"""
        print("🔍 Testing API Server...")
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{BASE_URL}/")
                if response.status_code == 200:
                    self.results["api_health"] = {
                        "status": "success",
                        "details": f"API server is running (status: {response.status_code})"
                    }
                    print("   ✅ API server is running")
                    return True
                else:
                    self.results["api_health"] = {
                        "status": "failed",
                        "details": f"API server returned status {response.status_code}"
                    }
                    print(f"   ❌ API server returned status {response.status_code}")
                    return False
        except httpx.ConnectError:
            self.results["api_health"] = {
                "status": "failed",
                "details": "API server is not running or not accessible"
            }
            print("   ❌ API server is not running or not accessible")
            return False
        except Exception as e:
            self.results["api_health"] = {
                "status": "failed",
                "details": f"API server test failed: {str(e)}"
            }
            print(f"   ❌ API server test failed: {str(e)}")
            return False

    async def test_health_endpoint(self):
        """Test the health endpoint specifically"""
        print("🔍 Testing Health Endpoint...")
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"   ✅ Health endpoint successful: {health_data}")
                    return health_data
                else:
                    print(f"   ❌ Health endpoint failed: {response.status_code}")
                    return None
        except Exception as e:
            print(f"   ❌ Health endpoint test failed: {str(e)}")
            return None

    async def test_api_endpoints(self):
        """Test major API endpoints"""
        print("🔍 Testing API Endpoints...")
        endpoint_tests = []
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                # Test 1: Root endpoint
                try:
                    response = await client.get(f"{BASE_URL}/")
                    endpoint_tests.append({
                        "endpoint": "GET /",
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code,
                        "response": response.json() if response.status_code == 200 else response.text
                    })
                except Exception as e:
                    endpoint_tests.append({
                        "endpoint": "GET /",
                        "status": "failed",
                        "error": str(e)
                    })

                # Test 2: Health endpoint
                try:
                    response = await client.get(f"{BASE_URL}/health")
                    endpoint_tests.append({
                        "endpoint": "GET /health",
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code,
                        "response": response.json() if response.status_code == 200 else response.text
                    })
                except Exception as e:
                    endpoint_tests.append({
                        "endpoint": "GET /health",
                        "status": "failed",
                        "error": str(e)
                    })

                # Test 3: API documentation
                try:
                    response = await client.get(f"{BASE_URL}/docs")
                    endpoint_tests.append({
                        "endpoint": "GET /docs",
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code
                    })
                except Exception as e:
                    endpoint_tests.append({
                        "endpoint": "GET /docs",
                        "status": "failed",
                        "error": str(e)
                    })

                # Test 4: Users endpoint (should fail without data)
                try:
                    response = await client.get(f"{BASE_URL}/api/v1/energy/users/")
                    endpoint_tests.append({
                        "endpoint": "GET /api/v1/energy/users/",
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code,
                        "response": response.json() if response.status_code == 200 else response.text
                    })
                except Exception as e:
                    endpoint_tests.append({
                        "endpoint": "GET /api/v1/energy/users/",
                        "status": "failed",
                        "error": str(e)
                    })

                # Test 5: Create user (test POST endpoint)
                try:
                    user_data = {
                        "username": "testuser",
                        "email": "test@example.com",
                        "full_name": "Test User",
                        "energy_goal_kwh": 800.0,
                        "preferred_energy_source": "mixed"
                    }
                    response = await client.post(f"{BASE_URL}/api/v1/energy/users/", json=user_data)
                    endpoint_tests.append({
                        "endpoint": "POST /api/v1/energy/users/",
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code,
                        "response": response.json() if response.status_code == 200 else response.text
                    })
                    
                    # If user creation was successful, store user data for further tests
                    if response.status_code == 200:
                        self.test_data["user"] = response.json()
                except Exception as e:
                    endpoint_tests.append({
                        "endpoint": "POST /api/v1/energy/users/",
                        "status": "failed",
                        "error": str(e)
                    })

        except Exception as e:
            endpoint_tests.append({
                "endpoint": "All endpoints",
                "status": "failed",
                "error": f"General API test failed: {str(e)}"
            })

        self.results["api_endpoints"] = {
            "status": "success" if any(test["status"] == "success" for test in endpoint_tests) else "failed",
            "details": endpoint_tests
        }
        
        success_count = sum(1 for test in endpoint_tests if test["status"] == "success")
        total_count = len(endpoint_tests)
        print(f"   📊 API Endpoints: {success_count}/{total_count} successful")
        
        return endpoint_tests

    async def test_error_handling(self):
        """Test error handling and edge cases"""
        print("🔍 Testing Error Handling...")
        error_tests = []
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                # Test 1: Non-existent endpoint
                try:
                    response = await client.get(f"{BASE_URL}/nonexistent")
                    error_tests.append({
                        "test": "Non-existent endpoint",
                        "expected_status": 404,
                        "actual_status": response.status_code,
                        "status": "success" if response.status_code == 404 else "failed"
                    })
                except Exception as e:
                    error_tests.append({
                        "test": "Non-existent endpoint",
                        "status": "failed",
                        "error": str(e)
                    })

                # Test 2: Invalid user ID
                try:
                    response = await client.get(f"{BASE_URL}/api/v1/energy/users/invalid-id")
                    error_tests.append({
                        "test": "Invalid user ID",
                        "expected_status": 404,
                        "actual_status": response.status_code,
                        "status": "success" if response.status_code == 404 else "failed"
                    })
                except Exception as e:
                    error_tests.append({
                        "test": "Invalid user ID",
                        "status": "failed",
                        "error": str(e)
                    })

                # Test 3: Invalid JSON in POST request
                try:
                    response = await client.post(
                        f"{BASE_URL}/api/v1/energy/users/",
                        data="invalid json",
                        headers={"Content-Type": "application/json"}
                    )
                    error_tests.append({
                        "test": "Invalid JSON",
                        "expected_status": 422,
                        "actual_status": response.status_code,
                        "status": "success" if response.status_code == 422 else "failed"
                    })
                except Exception as e:
                    error_tests.append({
                        "test": "Invalid JSON",
                        "status": "failed",
                        "error": str(e)
                    })

        except Exception as e:
            error_tests.append({
                "test": "Error handling tests",
                "status": "failed",
                "error": f"General error test failed: {str(e)}"
            })

        self.results["error_handling"] = {
            "status": "success" if any(test["status"] == "success" for test in error_tests) else "failed",
            "details": error_tests
        }
        
        success_count = sum(1 for test in error_tests if test["status"] == "success")
        total_count = len(error_tests)
        print(f"   📊 Error Handling: {success_count}/{total_count} successful")
        
        return error_tests

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📋 COMPREHENSIVE API & DATABASE TEST REPORT")
        print("="*60)
        
        # Overall status
        overall_success = all(
            result["status"] == "success" 
            for result in self.results.values() 
            if isinstance(result, dict) and "status" in result
        )
        
        self.results["overall_status"] = "success" if overall_success else "failed"
        
        print(f"\n🎯 Overall Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
        
        # Database connection
        db_status = self.results["database_connection"]["status"]
        print(f"\n🗄️  Database Connection: {'✅ SUCCESS' if db_status == 'success' else '❌ FAILED'}")
        print(f"   Details: {self.results['database_connection']['details']}")
        
        # API health
        api_status = self.results["api_health"]["status"]
        print(f"\n🌐 API Health: {'✅ SUCCESS' if api_status == 'success' else '❌ FAILED'}")
        print(f"   Details: {self.results['api_health']['details']}")
        
        # API endpoints
        endpoints_status = self.results["api_endpoints"]["status"]
        print(f"\n🔗 API Endpoints: {'✅ SUCCESS' if endpoints_status == 'success' else '❌ FAILED'}")
        if "details" in self.results["api_endpoints"]:
            for test in self.results["api_endpoints"]["details"]:
                status_icon = "✅" if test["status"] == "success" else "❌"
                print(f"   {status_icon} {test['endpoint']} - Status: {test.get('status_code', 'N/A')}")
        
        # Error handling
        error_status = self.results["error_handling"]["status"]
        print(f"\n⚠️  Error Handling: {'✅ SUCCESS' if error_status == 'success' else '❌ FAILED'}")
        if "details" in self.results["error_handling"]:
            for test in self.results["error_handling"]["details"]:
                status_icon = "✅" if test["status"] == "success" else "❌"
                print(f"   {status_icon} {test['test']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if db_status != "success":
            print("   • Install and start MongoDB server")
            print("   • Check MongoDB connection string in configuration")
            print("   • Verify MongoDB is accessible on localhost:27017")
        
        if api_status != "success":
            print("   • Start the FastAPI server using: python3 -m uvicorn app.main:app --reload")
            print("   • Check if the server is running on port 8000")
            print("   • Verify all dependencies are installed")
        
        if endpoints_status != "success":
            print("   • Check API endpoint implementations")
            print("   • Verify request/response models are correct")
            print("   • Test with valid data")
        
        if error_status != "success":
            print("   • Improve error handling in API endpoints")
            print("   • Add proper validation for input data")
            print("   • Implement consistent error responses")
        
        print(f"\n📖 API Documentation: {BASE_URL}/docs")
        print("="*60)
        
        return self.results

    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive API & Database Tests...\n")
        
        # Test database connection
        await self.test_database_connection()
        
        # Test API server
        await self.test_api_server_running()
        
        # Test health endpoint
        health_data = await self.test_health_endpoint()
        
        # Test API endpoints
        await self.test_api_endpoints()
        
        # Test error handling
        await self.test_error_handling()
        
        # Generate report
        return self.generate_report()

async def main():
    """Main test function"""
    tester = APITester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if results["overall_status"] == "success":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())