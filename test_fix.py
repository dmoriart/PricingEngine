#!/usr/bin/env python3
"""
Quick test for the fixed RAROC endpoint
"""
import requests
import json

def test_raroc_endpoint():
    """Test the fixed RAROC calculation."""
    url = "http://localhost:8000/raroc/calculate"
    
    data = {
        "borrowers": [{
            "borrower_id": "TEST-001",
            "borrower_name": "Test Company",
            "credit_score": 720,
            "debt_to_income": 0.3,
            "loan_to_value": 0.8,
            "employment_years": 5,
            "payment_history_score": 80,
            "industry": "technology",
            "company_size": "medium",
            "collateral_type": "real_estate",
            "seniority": "senior_secured",
            "facility_type": "term_loan",
            "exposure_amount": 250000,
            "outstanding_amount": 200000,
            "undrawn_amount": 50000,
            "loan_term": 5,
            "region": "north_america"
        }]
    }
    
    try:
        print("🧪 Testing RAROC endpoint with fixed code...")
        response = requests.post(url, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAROC calculation successful!")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    test_raroc_endpoint()
