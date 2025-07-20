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
python main.py
```

#### Test Endpoints:

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Sample Pricing:**
```bash
curl http://localhost:8000/pricing/sample | python -m json.tool
```

**Custom Pricing:**
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
python test_api_client.py
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

✅ **Unit Tests**: 5/5 passing  
✅ **API Health Check**: Working  
✅ **Sample Pricing**: Working  
✅ **Custom Pricing**: Working  
✅ **Coverage**: 36% (pricing module)  

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
