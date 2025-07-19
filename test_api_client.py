#!/usr/bin/env python3
"""
Simple test script to verify PricingEngine functionality
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Health check failed: {e}")
        return False

def test_sample_pricing():
    """Test the sample pricing endpoint"""
    try:
        response = requests.get(f"{API_BASE}/pricing/sample", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Sample pricing successful!")
            print(f"Total products: {data['summary']['total_products']}")
            print(f"Total revenue: ${data['summary']['total_revenue']:.2f}")
            print(f"Average price: ${data['summary']['average_price']:.2f}")
            return True
        else:
            print(f"Sample pricing failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Sample pricing failed: {e}")
        return False

def test_custom_pricing():
    """Test custom pricing calculation"""
    test_data = {
        "products": [
            {
                "product_id": "TEST001",
                "name": "Test Widget",
                "category": "premium",
                "cost": 100.0,
                "quantity": 150
            },
            {
                "product_id": "TEST002",
                "name": "Standard Widget",
                "category": "standard",
                "cost": 75.0,
                "quantity": 75
            }
        ],
        "pricing_rules": {
            "premium_multiplier": 2.5,
            "standard_multiplier": 1.8,
            "basic_multiplier": 1.3
        },
        "discount_rules": {
            "bulk_threshold": 100,
            "bulk_discount": 0.15,
            "medium_threshold": 50,
            "medium_discount": 0.08
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/pricing/calculate", 
            json=test_data,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Custom pricing successful!")
            print(f"Products processed: {len(data['products'])}")
            for product in data['products']:
                print(f"  {product['name']}: ${product['final_price']:.2f} (was ${product['cost']:.2f})")
            return True
        else:
            print(f"Custom pricing failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Custom pricing failed: {e}")
        return False

def main():
    """Main test function"""
    print("=== PricingEngine API Test ===")
    print("\nMake sure the API server is running with: python main.py")
    print("Then run this test script to verify functionality.\n")
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    if not test_health():
        print("❌ Health check failed. Is the server running?")
        return
    
    print("✅ Health check passed")
    
    # Test sample pricing
    print("\n2. Testing sample pricing...")
    if test_sample_pricing():
        print("✅ Sample pricing passed")
    else:
        print("❌ Sample pricing failed")
    
    # Test custom pricing
    print("\n3. Testing custom pricing...")
    if test_custom_pricing():
        print("✅ Custom pricing passed")
    else:
        print("❌ Custom pricing failed")
    
    print("\n=== Test Complete ===")
    print("Visit http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    main()
