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


def test_raroc_sample_pricing():
    """Test the RAROC sample pricing endpoint."""
    response = client.get("/raroc/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "summary" in data
    assert "borrowers" in data
    assert "model_info" in data
    assert len(data["borrowers"]) > 0
    
    # Check summary contains expected fields
    summary = data["summary"]
    expected_fields = ["total_exposure", "portfolio_raroc", "average_pd", "average_lgd"]
    for field in expected_fields:
        assert field in summary
    
    # Check model info
    model_info = data["model_info"]
    assert model_info["pd_model"] == "logistic"
    assert model_info["lgd_model"] == "hybrid"
    assert model_info["risk_type"] == "corporate"


def test_raroc_calculation():
    """Test the RAROC calculation endpoint."""
    test_request = {
        "borrowers": [
            {
                "borrower_id": "TEST001",
                "borrower_name": "Test Company",
                "credit_score": 720,
                "debt_to_income": 0.4,
                "loan_to_value": 0.75,
                "employment_years": 8,
                "payment_history_score": 85,
                "industry": "technology",
                "company_size": "medium",
                "collateral_type": "equipment",
                "seniority": "senior_secured",
                "facility_type": "term_loan",
                "exposure_amount": 1000000.0,
                "outstanding_amount": 1000000.0,
                "undrawn_amount": 0.0,
                "loan_term": 5,
                "region": "developed"
            }
        ],
        "pd_model": "logistic",
        "lgd_model": "hybrid",
        "risk_type": "corporate",
        "target_raroc": 0.15
    }
    
    response = client.post("/raroc/calculate", json=test_request)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["borrowers"]) == 1
    
    borrower = data["borrowers"][0]
    assert borrower["borrower_id"] == "TEST001"
    
    # Check that key risk metrics are calculated
    expected_fields = ["pd_score", "lgd_score", "ead_amount", "raroc", "minimum_rate"]
    for field in expected_fields:
        assert field in borrower
        assert isinstance(borrower[field], (int, float))
    
    # Check risk bounds
    assert 0 <= borrower["pd_score"] <= 1
    assert 0 <= borrower["lgd_score"] <= 1
    assert borrower["ead_amount"] > 0
    assert borrower["minimum_rate"] > 0


def test_raroc_models_info():
    """Test the RAROC models information endpoint."""
    response = client.get("/raroc/models")
    assert response.status_code == 200
    data = response.json()
    
    # Check PD models
    assert "pd_models" in data
    pd_models = data["pd_models"]
    expected_pd_models = ["logistic", "score_based", "industry"]
    for model in expected_pd_models:
        assert model in pd_models
    
    # Check LGD models
    assert "lgd_models" in data
    lgd_models = data["lgd_models"]
    expected_lgd_models = ["collateral", "industry", "hybrid"]
    for model in expected_lgd_models:
        assert model in lgd_models
    
    # Check risk types and economic conditions
    assert "risk_types" in data
    assert "economic_conditions" in data


def test_raroc_benchmark():
    """Test the RAROC model benchmarking endpoint."""
    test_borrowers = [
        {
            "borrower_id": "B001",
            "borrower_name": "Company A",
            "credit_score": 750,
            "debt_to_income": 0.35,
            "loan_to_value": 0.70,
            "employment_years": 10,
            "payment_history_score": 90,
            "industry": "technology",
            "company_size": "large",
            "collateral_type": "equipment",
            "seniority": "senior_secured",
            "facility_type": "term_loan",
            "exposure_amount": 5000000.0,
            "outstanding_amount": 5000000.0,
            "undrawn_amount": 0.0,
            "loan_term": 5,
            "region": "developed"
        },
        {
            "borrower_id": "B002",
            "borrower_name": "Company B",
            "credit_score": 680,
            "debt_to_income": 0.45,
            "loan_to_value": 0.80,
            "employment_years": 6,
            "payment_history_score": 75,
            "industry": "manufacturing",
            "company_size": "medium",
            "collateral_type": "real_estate",
            "seniority": "senior_secured",
            "facility_type": "revolving_credit",
            "exposure_amount": 2000000.0,
            "outstanding_amount": 1500000.0,
            "undrawn_amount": 500000.0,
            "loan_term": 3,
            "region": "developed"
        }
    ]
    
    response = client.post("/raroc/benchmark", json=test_borrowers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "benchmark_results" in data
    assert "models_compared" in data
    
    # Check that multiple model combinations are benchmarked
    benchmark_results = data["benchmark_results"]
    assert len(benchmark_results) > 1
    
    # Each benchmark result should contain key metrics
    for model_combo, metrics in benchmark_results.items():
        expected_metrics = ["portfolio_raroc", "average_minimum_rate", "expected_loss_rate"]
        for metric in expected_metrics:
            assert metric in metrics


def test_invalid_raroc_request():
    """Test RAROC calculation with invalid data."""
    invalid_request = {
        "borrowers": [
            {
                "borrower_id": "INVALID",
                "credit_score": 1000,  # Invalid credit score
                "debt_to_income": -0.5  # Invalid DTI
            }
        ]
    }
    
    response = client.post("/raroc/calculate", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_metrics_endpoint():
    """Test the metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    
    expected_fields = ["spark_app_name", "spark_master", "api_version", "debug_mode"]
    for field in expected_fields:
        assert field in data
