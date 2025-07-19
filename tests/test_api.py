import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_sample_pricing():
    """Test the sample pricing endpoint."""
    response = client.get("/pricing/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "summary" in data
    assert "products" in data
    assert len(data["products"]) > 0


def test_pricing_calculation():
    """Test the pricing calculation endpoint."""
    test_request = {
        "products": [
            {
                "product_id": "TEST001",
                "name": "Test Product",
                "category": "standard",
                "cost": 100.0,
                "quantity": 50
            }
        ],
        "pricing_rules": {
            "premium_multiplier": 2.0,
            "standard_multiplier": 1.5,
            "basic_multiplier": 1.2
        },
        "discount_rules": {
            "bulk_threshold": 100,
            "bulk_discount": 0.1,
            "medium_threshold": 50,
            "medium_discount": 0.05
        }
    }
    
    response = client.post("/pricing/calculate", json=test_request)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["products"]) == 1
    
    product = data["products"][0]
    assert product["product_id"] == "TEST001"
    assert product["base_price"] == 150.0  # 100 * 1.5 (standard multiplier)
    assert product["final_price"] == 142.5  # 150 * (1 - 0.05) (medium discount)
