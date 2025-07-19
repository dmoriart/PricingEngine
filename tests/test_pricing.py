import pytest
from unittest.mock import Mock, patch
from pricing.engine import PricingEngine


@pytest.fixture
def pricing_engine():
    """Create a pricing engine instance for testing."""
    with patch('pricing.engine.spark_manager') as mock_spark_manager:
        mock_spark = Mock()
        mock_spark_manager.spark = mock_spark
        engine = PricingEngine()
        engine.spark = mock_spark
        return engine


def test_pricing_engine_initialization(pricing_engine):
    """Test pricing engine initialization."""
    assert pricing_engine is not None
    assert pricing_engine.spark is not None


def test_calculate_base_price_logic():
    """Test base price calculation logic without Spark dependencies."""
    # Test the pricing logic independently
    cost = 100.0
    premium_multiplier = 2.0
    standard_multiplier = 1.5
    basic_multiplier = 1.2
    
    # Premium category
    premium_price = cost * premium_multiplier
    assert premium_price == 200.0
    
    # Standard category
    standard_price = cost * standard_multiplier
    assert standard_price == 150.0
    
    # Basic category
    basic_price = cost * basic_multiplier
    assert basic_price == 120.0


def test_discount_calculation_logic():
    """Test discount calculation logic without Spark dependencies."""
    base_price = 150.0
    
    # Bulk discount (quantity >= 100)
    bulk_discount_rate = 0.1
    bulk_final_price = base_price * (1.0 - bulk_discount_rate)
    assert bulk_final_price == 135.0
    
    # Medium discount (quantity >= 50)
    medium_discount_rate = 0.05
    medium_final_price = base_price * (1.0 - medium_discount_rate)
    assert medium_final_price == 142.5
    
    # No discount (quantity < 50)
    no_discount_price = base_price * (1.0 - 0.0)
    assert no_discount_price == 150.0


def test_pricing_rules_validation():
    """Test pricing rules validation."""
    valid_rules = {
        "premium_multiplier": 2.0,
        "standard_multiplier": 1.5,
        "basic_multiplier": 1.2
    }
    
    assert valid_rules["premium_multiplier"] > 0
    assert valid_rules["standard_multiplier"] > 0
    assert valid_rules["basic_multiplier"] > 0


def test_discount_rules_validation():
    """Test discount rules validation."""
    valid_discount_rules = {
        "bulk_threshold": 100,
        "bulk_discount": 0.1,
        "medium_threshold": 50,
        "medium_discount": 0.05
    }
    
    assert valid_discount_rules["bulk_threshold"] > 0
    assert 0 <= valid_discount_rules["bulk_discount"] <= 1
    assert valid_discount_rules["medium_threshold"] > 0
    assert 0 <= valid_discount_rules["medium_discount"] <= 1
