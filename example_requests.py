#!/usr/bin/env python3
"""
Example API requests for both pricing endpoints.
This shows the correct data format for each endpoint.
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_traditional_pricing():
    """Test the traditional /pricing/calculate endpoint."""
    print("🧪 Testing Traditional Pricing Endpoint: /pricing/calculate")
    
    # Traditional pricing expects products data
    data = {
        "products": [
            {
                "product_id": "PROD-001",
                "name": "Business Loan",
                "category": "standard",
                "cost": 100000.0,
                "quantity": 1
            },
            {
                "product_id": "PROD-002", 
                "name": "Equipment Financing",
                "category": "premium",
                "cost": 250000.0,
                "quantity": 2
            }
        ],
        "pricing_rules": {
            "base_margin": 0.15,
            "premium_multiplier": 1.2,
            "standard_multiplier": 1.0,
            "basic_multiplier": 0.8
        },
        "discount_rules": {
            "bulk_threshold": 100,
            "bulk_discount": 0.1,
            "medium_threshold": 50,
            "medium_discount": 0.05
        }
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/pricing/calculate", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Traditional Pricing Success!")
            print(f"Total Products: {len(result.get('products', []))}")
            print(f"Summary: {result.get('summary', {})}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_raroc_pricing():
    """Test the RAROC /raroc/calculate endpoint."""
    print("\n🧪 Testing RAROC Pricing Endpoint: /raroc/calculate")
    
    # RAROC pricing expects borrowers data
    data = {
        "borrowers": [
            {
                "borrower_id": "BORR-001",
                "borrower_name": "Tech Corp Inc",
                "credit_score": 720,
                "debt_to_income": 0.35,
                "loan_to_value": 0.75,
                "employment_years": 5,
                "payment_history_score": 85,
                "industry": "technology",
                "company_size": "medium",
                "collateral_type": "real_estate",
                "seniority": "senior_secured",
                "facility_type": "term_loan",
                "exposure_amount": 500000.0,
                "outstanding_amount": 400000.0,
                "undrawn_amount": 100000.0,
                "loan_term": 5,
                "region": "north_america"
            }
        ],
        "pd_model": "logistic",
        "lgd_model": "hybrid",
        "risk_type": "corporate",
        "target_raroc": 0.15,
        "competitive_margin": 0.02
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/raroc/calculate", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAROC Pricing Success!")
            print(f"Total Borrowers: {len(result.get('borrowers', []))}")
            print(f"Summary: {result.get('summary', {})}")
            
            if result.get('borrowers'):
                borrower = result['borrowers'][0]
                print(f"Sample Borrower Results:")
                print(f"  - PD: {borrower.get('pd', 'N/A')}")
                print(f"  - LGD: {borrower.get('lgd', 'N/A')}")
                print(f"  - RAROC: {borrower.get('raroc', 'N/A')}")
                print(f"  - Recommended Rate: {borrower.get('recommended_rate', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_simple_raroc():
    """Test a simplified RAROC request that's easier to use."""
    print("\n🧪 Testing Simplified RAROC Request")
    
    # Simpler request using the existing /raroc/sample endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/raroc/sample")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Sample RAROC Success!")
            print(f"Portfolio Summary: {result}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 API Endpoint Examples\n")
    print("=" * 50)
    
    # Test both endpoints to show the difference
    test_traditional_pricing()
    test_raroc_pricing()
    test_simple_raroc()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("- Use /pricing/calculate for traditional product pricing")
    print("- Use /raroc/calculate for risk-based borrower pricing")
    print("- Use /raroc/sample for quick portfolio analysis")
