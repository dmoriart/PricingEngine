# 🧪 PricingEngine Testing Guide

## Quick Testing Commands

### 1. **Unit Tests**
```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_pricing.py -v
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=. --cov-report=html -v

# Run tests and generate coverage report
pytest --cov=pricing --cov-report=term-missing -v
```

### 2. **API Testing (Manual)**

#### Start the Server:
```bash
# Method 1: Using uvicorn module (recommended)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Method 2: Using the startup script
python start_server.py
```

#### Test Endpoints:

**Health Check:**
```bash
curl http://localhost:8000/health
```

**RAROC Sample Portfolio:**
```bash
curl http://localhost:8000/raroc/sample | python -m json.tool
```

**RAROC Risk-Based Pricing:**
```bash
curl -X POST http://localhost:8000/raroc/calculate \
  -H "Content-Type: application/json" \
  -d '{
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
  }' | python -m json.tool
```

**Traditional Product Pricing:**
```bash
curl -X POST http://localhost:8000/pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {
        "product_id": "TEST001",
        "name": "Test Product",
        "category": "premium",
        "cost": 100.0,
        "quantity": 120
      }
    ]
  }' | python -m json.tool
```

### 3. **Automated API Testing**
```bash
# Test the quick RAROC fix
python test_fix.py

# Test all endpoints
python test_api_client.py

# Test examples
python example_requests.py
```

### 4. **VS Code Testing**

#### Use Tasks (Ctrl+Shift+P → "Tasks: Run Task"):
- **Run Tests** - Execute pytest
- **Run Tests with Coverage** - Tests with coverage report

#### Use Debug Configuration (F5):
- **Python: Pytest** - Debug test execution

### 5. **Code Quality Checks**
```bash
# Format code
black .

# Check code style
flake8 .

# Type checking
mypy --ignore-missing-imports .
```

## Test Results Summary

✅ **Unit Tests**: 19/19 RAROC tests passing  
✅ **API Health Check**: Working  
✅ **RAROC Pricing**: Working (Fixed 'str' object error)  
✅ **Traditional Pricing**: Working  
✅ **Coverage**: Comprehensive risk model coverage  

## Recent Fixes Applied

🔧 **Fixed 'str' object has no attribute 'name' error**:
- Updated all DataFrame column checking from `[c.name for c in df.columns]` to `df.columns`
- Applied to: `pd_models.py`, `lgd_models.py`, `raroc_calculator.py`
- RAROC calculations now work correctly  

## Interactive API Documentation

Visit these URLs when the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Performance Testing

### Basic Load Test:
```bash
# Install apache bench (if not installed)
# brew install httpd (on macOS)

# Test 100 requests with 10 concurrent
ab -n 100 -c 10 http://localhost:8000/health
```

### PySpark Performance Test:
```bash
python -c "
from pricing.engine import PricingEngine
engine = PricingEngine()
sample_df = engine.create_sample_data()
print('Sample data created successfully')
print(f'Row count: {sample_df.count()}')
"
```

## Common Issues & Solutions

### 1. **Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt
```

### 2. **Java Not Found (PySpark)**
```bash
# Install Java (required for PySpark)
# macOS: brew install openjdk@11
# Ubuntu: sudo apt install openjdk-11-jdk
```

### 3. **Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### 4. **Server Not Starting**
```bash
# Check logs
tail -f server.log

# Check if all dependencies are installed
pip list | grep -E "(fastapi|pyspark|uvicorn)"
```

## Test Data Examples

### Pricing Rules:
```json
{
  "premium_multiplier": 2.5,
  "standard_multiplier": 1.8,
  "basic_multiplier": 1.3
}
```

### Discount Rules:
```json
{
  "bulk_threshold": 100,
  "bulk_discount": 0.15,
  "medium_threshold": 50,
  "medium_discount": 0.08
}
```

### Sample Product:
```json
{
  "product_id": "TEST001",
  "name": "Test Widget",
  "category": "premium",
  "cost": 100.0,
  "quantity": 150
}
```

## Next Steps

1. **Increase Test Coverage**: Add more unit tests for edge cases
2. **Integration Tests**: Test with real databases
3. **Performance Tests**: Load testing with large datasets
4. **End-to-End Tests**: Complete workflow testing
5. **Mock Tests**: Test external dependencies
