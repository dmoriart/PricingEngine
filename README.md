# PricingEngine

A sophisticated risk-based pricing engine built with PySpark and FastAPI, featuring **RAROC (Risk-Adjusted Return on Capital)** methodology for advanced financial risk pricing.

## Features

- **RAROC-Based Pricing**: Calculate risk-adjusted returns using PD, LGD, and EAD models
- **Multiple Risk Models**: Logistic regression, score-based, and industry-specific PD models
- **Collateral Analysis**: Sophisticated LGD models based on collateral type and coverage
- **Distributed Processing**: Uses PySpark for handling large-scale pricing calculations
- **REST API**: FastAPI-based endpoints with automatic documentation
- **Real-time Processing**: Process pricing requests in real-time via API
- **Model Benchmarking**: Compare different risk model combinations
- **Stress Testing**: Built-in stress testing capabilities
- **Comprehensive Testing**: Full test coverage for business logic and API endpoints

## Risk Models

### **Probability of Default (PD) Models**
- **Logistic Model**: Multi-factor logistic regression with credit score, DTI, LTV, employment history
- **Score-Based Model**: Credit score buckets with industry-calibrated default rates
- **Industry Model**: Sector-specific PD rates with size and geographic adjustments

### **Loss Given Default (LGD) Models**
- **Collateral Model**: Recovery rates by asset type (real estate, equipment, inventory, etc.)
- **Industry Model**: Sector-based recovery characteristics
- **Hybrid Model**: Weighted combination of collateral and industry factors

### **RAROC Components**
- **EAD Calculation**: Exposure at Default with credit conversion factors
- **Capital Allocation**: Regulatory and economic capital requirements
- **Expected Loss**: PD × LGD × EAD
- **Minimum Pricing**: Cost of capital + expected loss + operational costs

## Architecture

```
PricingEngine/
├── api/                    # FastAPI application and endpoints
│   ├── __init__.py
│   └── main.py            # Main API with RAROC and traditional pricing
├── config/                # Configuration management
│   ├── __init__.py
│   └── settings.py        # Environment-based settings
├── core/                  # Core utilities and Spark management
│   ├── __init__.py
│   └── spark_manager.py   # Spark session management
├── pricing/               # Traditional pricing calculations
│   ├── __init__.py
│   └── engine.py          # Basic pricing engine with PySpark
├── risk/                  # RAROC and risk management modules
│   ├── __init__.py
│   ├── pd_models.py       # Probability of Default models
│   ├── lgd_models.py      # Loss Given Default models
│   ├── raroc_calculator.py # RAROC computation engine
│   └── raroc_pricing_engine.py # Main RAROC pricing engine
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_api.py        # API endpoint tests (traditional + RAROC)
│   ├── test_pricing.py    # Traditional pricing logic tests
│   └── test_raroc.py      # RAROC and risk model tests
├── .github/
│   └── copilot-instructions.md  # Copilot customization
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── TESTING.md            # Comprehensive testing guide
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

#### Traditional Pricing
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/pricing/sample` | GET | Demo pricing calculation |
| `/pricing/calculate` | POST | Custom pricing calculation |

#### RAROC Risk-Based Pricing
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/raroc/sample` | GET | Demo RAROC pricing with sample portfolio |
| `/raroc/calculate` | POST | Custom RAROC pricing calculation |
| `/raroc/benchmark` | POST | Benchmark different PD/LGD model combinations |
| `/raroc/models` | GET | Available risk models information |
| `/metrics` | GET | Application metrics |

## Quick Start

### Prerequisites

- Python 3.8+
- Java 8+ (required for PySpark)

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone https://github.com/dmoriart/PricingEngine.git
   cd PricingEngine
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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

### RAROC Pricing Examples

#### Sample RAROC Calculation
```bash
curl http://localhost:8000/raroc/sample
```

#### Custom RAROC Pricing
```bash
curl -X POST http://localhost:8000/raroc/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "borrowers": [
      {
        "borrower_id": "B001",
        "borrower_name": "TechCorp Inc",
        "credit_score": 750,
        "debt_to_income": 0.35,
        "loan_to_value": 0.75,
        "employment_years": 8,
        "payment_history_score": 95,
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
      }
    ],
    "pd_model": "logistic",
    "lgd_model": "hybrid",
    "target_raroc": 0.15
  }'
```

#### Model Benchmarking
```bash
curl -X POST http://localhost:8000/raroc/benchmark \
  -H "Content-Type: application/json" \
  -d '[
    {
      "borrower_id": "B001",
      "borrower_name": "Company A",
      "credit_score": 720,
      "debt_to_income": 0.4,
      "loan_to_value": 0.8,
      "employment_years": 10,
      "payment_history_score": 85,
      "industry": "manufacturing",
      "company_size": "medium",
      "collateral_type": "real_estate",
      "seniority": "senior_secured", 
      "facility_type": "term_loan",
      "exposure_amount": 2000000.0,
      "outstanding_amount": 2000000.0,
      "undrawn_amount": 0.0,
      "loan_term": 7,
      "region": "developed"
    }
  ]'
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

## RAROC Methodology

The PricingEngine implements a comprehensive RAROC framework:

### **Risk Components**
- **PD (Probability of Default)**: Likelihood of borrower default within 1 year
- **LGD (Loss Given Default)**: Expected loss rate if default occurs  
- **EAD (Exposure at Default)**: Total exposure amount at time of default
- **Expected Loss**: PD × LGD × EAD

### **Capital Allocation**
- **Regulatory Capital**: Basel III compliant capital requirements
- **Economic Capital**: Internal risk-based capital allocation
- **Capital Cost**: Target return on allocated capital

### **RAROC Formula**
```
RAROC = (Revenue - Expected Loss - Funding Cost - Operational Cost) / Economic Capital

Where:
- Revenue = Interest Income + Fee Income
- Expected Loss = PD × LGD × EAD  
- Funding Cost = EAD × Funding Rate
- Operational Cost = EAD × Operational Rate
- Economic Capital = Regulatory Capital × Economic Multiplier
```

### **Pricing Decision Framework**
| RAROC Range | Recommendation | Action |
|-------------|----------------|---------|
| ≥ 22.5% | HIGHLY_ATTRACTIVE | Aggressively pursue |
| 15-22.5% | ATTRACTIVE | Standard approval |
| 12-15% | ACCEPTABLE | Conditional approval |
| 7.5-12% | MARGINAL | Enhanced monitoring |
| < 7.5% | REJECT | Decline or re-price |

## Risk Model Details

### **PD Models**

#### Logistic Regression Model
- **Features**: Credit score, DTI, LTV, employment years, payment history
- **Coefficients**: Calibrated from historical default data
- **Output**: Probability score between 0.1% and 99%

#### Score-Based Model  
- **Input**: Credit score (300-850)
- **Mapping**: Score ranges to historical default rates
- **Adjustments**: DTI and other risk factors

#### Industry Model
- **Sectors**: Technology, healthcare, manufacturing, retail, energy, etc.
- **Base Rates**: Industry-specific default probabilities
- **Adjustments**: Company size, geography

### **LGD Models**

#### Collateral-Based Model
- **Asset Types**: Real estate, equipment, inventory, cash, unsecured
- **Recovery Rates**: Historical recovery by collateral type
- **LTV Impact**: Loan-to-value ratio adjustments
- **Seniority**: Senior secured, senior unsecured, subordinated

#### Industry Model
- **Asset Tangibility**: Industry-specific asset liquidity
- **Market Conditions**: Economic cycle adjustments
- **Company Size**: Scale effects on recovery

#### Hybrid Model
- **Combination**: 60% collateral + 40% industry factors
- **Optimization**: Weighted approach for best accuracy

## Testing

### **Unit Tests**
```bash
# All tests
pytest -v

# RAROC-specific tests  
pytest tests/test_raroc.py -v

# API tests including RAROC endpoints
pytest tests/test_api.py -v

# Traditional pricing tests
pytest tests/test_pricing.py -v
```

### **Coverage Analysis**
```bash
pytest --cov=. --cov-report=html -v
```

### **Model Validation**
```bash
# Test all model combinations
python -c "
from risk.raroc_pricing_engine import RARoCPricingEngine
engine = RARoCPricingEngine()
portfolio = engine.create_sample_portfolio()
results = engine.benchmark_pricing_models(portfolio)
print('Model benchmarking completed:', len(results), 'combinations tested')
"
```
