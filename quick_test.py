#!/usr/bin/env python3
"""
Quick test to verify the API server is running and responding.
"""
import requests
import json

def test_server():
    """Test if the server is responding."""
    try:
        # Test health endpoint
        print("🧪 Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Server is running and healthy!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on port 8000?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server timeout. Server might be starting up...")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_simple_raroc():
    """Test the RAROC sample endpoint."""
    try:
        print("\n🧪 Testing RAROC sample endpoint...")
        response = requests.get("http://localhost:8000/raroc/sample", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAROC endpoint working!")
            print(f"Portfolio size: {result.get('total_borrowers', 'N/A')}")
            print(f"Average RAROC: {result.get('average_raroc', 'N/A')}%")
            return True
        else:
            print(f"❌ RAROC test failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ RAROC test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing PricingEngine API Server\n")
    
    # Test basic connectivity
    if test_server():
        # Test RAROC functionality
        test_simple_raroc()
        print("\n🎉 Server is working! You can now:")
        print("- Visit http://localhost:8000/docs for API documentation")
        print("- Use the API endpoints for pricing calculations")
    else:
        print("\n⚠️  Server is not responding. Make sure it's running with:")
        print("python start_server.py")
