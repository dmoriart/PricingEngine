# PricingEngine

A high-performance pricing engine built with PySpark and FastAPI for scalable price calculations and API services.

## Features

- **Distributed Processing**: Uses PySpark for handling large-scale pricing calculations
- **REST API**: FastAPI-based endpoints with automatic documentation
- **Flexible Pricing Rules**: Configurable pricing multipliers and discount rules
- **Real-time Processing**: Process pricing requests in real-time via API
- **Comprehensive Testing**: Full test coverage for business logic and API endpoints
- **Docker Ready**: Containerized deployment with Docker support

## Architecture

```
PricingEngine/
├── api/                    # FastAPI application and endpoints
│   ├── __init__.py
│   └── main.py            # Main API application with endpoints
├── config/                # Configuration management
│   ├── __init__.py
│   └── settings.py        # Environment-based settings
├── core/                  # Core utilities and Spark management
│   ├── __init__.py
│   └── spark_manager.py   # Spark session management
├── pricing/               # Business logic for pricing calculations
│   ├── __init__.py
│   └── engine.py          # Main pricing engine with PySpark
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_api.py        # API endpoint tests
│   └── test_pricing.py    # Pricing logic tests
├── .github/
│   └── copilot-instructions.md  # Copilot customization
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── main.py               # Application entry point
```

## Quick Start

### Prerequisites

- Python 3.8+
- Java 8+ (required for PySpark)

### Installation

1. **Clone and setup the project:**
   ```bash
   cd /Users/desmoriarty/OneDrive/Python/PricingEngine
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

### Running the Application

1. **Start the API server:**
   ```bash
   python main.py
   ```

2. **Access the API:**
   - API Base URL: http://localhost:8000
   - Interactive Documentation: http://localhost:8000/docs
   - OpenAPI Schema: http://localhost:8000/redoc

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Sample Pricing
```bash
curl http://localhost:8000/pricing/sample
```

#### Custom Pricing Calculation
```bash
curl -X POST http://localhost:8000/pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {
        "product_id": "P001",
        "name": "Widget",
        "category": "premium",
        "cost": 100.0,
        "quantity": 150
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
  }'
```

## Configuration

The application uses environment variables for configuration. Key settings include:

- `DEBUG`: Enable debug mode (default: False)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `SPARK_MASTER`: Spark master URL (default: local[*])
- `SPARK_DRIVER_MEMORY`: Spark driver memory (default: 2g)
- `SPARK_EXECUTOR_MEMORY`: Spark executor memory (default: 2g)

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## Development

### Code Style

The project follows PEP 8 guidelines. Format code using:

```bash
black .
flake8 .
mypy .
```

### Adding New Features

1. Implement business logic in the `pricing/` module
2. Add API endpoints in `api/main.py`
3. Write comprehensive tests in `tests/`
4. Update documentation

## Pricing Logic

The engine supports:

- **Category-based pricing**: Different multipliers for basic, standard, and premium products
- **Volume discounts**: Automatic discounts based on quantity thresholds
- **Flexible rules**: Configurable pricing and discount parameters
- **Real-time processing**: Instant price calculations via API

## Performance

- **PySpark**: Distributed processing for large datasets
- **FastAPI**: High-performance async API framework
- **Caching**: Spark DataFrame caching for frequently accessed data
- **Optimization**: SQL query optimization and adaptive query execution

## License

This project is licensed under the MIT License.

## Support

For questions and support, please refer to the project documentation or create an issue in the repository.
