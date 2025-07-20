from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
from contextlib import asynccontextmanager

from config.settings import settings
from pricing.engine import PricingEngine
from risk.raroc_pricing_engine import RARoCPricingEngine
from core.spark_manager import spark_manager

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ProductRequest(BaseModel):
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category (basic, standard, premium)")
    cost: float = Field(..., gt=0, description="Product cost")
    quantity: int = Field(..., gt=0, description="Quantity")

class BorrowerRequest(BaseModel):
    borrower_id: str = Field(..., description="Unique borrower identifier")
    borrower_name: str = Field(..., description="Borrower name")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (300-850)")
    debt_to_income: float = Field(..., ge=0, le=2, description="Debt-to-income ratio")
    loan_to_value: float = Field(..., ge=0, le=1.5, description="Loan-to-value ratio")
    employment_years: int = Field(..., ge=0, description="Years of employment")
    payment_history_score: int = Field(..., ge=0, le=100, description="Payment history score")
    industry: str = Field(..., description="Industry sector")
    company_size: str = Field(..., description="Company size (small, medium, large)")
    collateral_type: str = Field(..., description="Type of collateral")
    seniority: str = Field(..., description="Loan seniority (senior_secured, senior_unsecured, subordinated)")
    facility_type: str = Field(..., description="Facility type (term_loan, revolving_credit, etc.)")
    exposure_amount: float = Field(..., gt=0, description="Total exposure amount")
    outstanding_amount: float = Field(..., ge=0, description="Outstanding amount")
    undrawn_amount: float = Field(..., ge=0, description="Undrawn amount")
    loan_term: int = Field(..., gt=0, description="Loan term in years")
    region: str = Field(..., description="Geographic region")

class RARoCPricingRequest(BaseModel):
    borrowers: List[BorrowerRequest] = Field(..., description="List of borrowers to price")
    pd_model: str = Field("logistic", description="PD model (logistic, score_based, industry)")
    lgd_model: str = Field("hybrid", description="LGD model (collateral, industry, hybrid)")
    risk_type: str = Field("corporate", description="Risk type for capital calculation")
    target_raroc: float = Field(0.15, gt=0, description="Target RAROC threshold")
    competitive_margin: float = Field(0.02, ge=0, description="Competitive margin over minimum rate")
    stress_pd_factor: float = Field(2.0, gt=0, description="PD stress factor")
    stress_lgd_factor: float = Field(1.3, gt=0, description="LGD stress factor")
    economic_condition: str = Field("normal", description="Economic condition (recession, normal, expansion)")

class PricingRulesRequest(BaseModel):
    premium_multiplier: float = Field(2.0, gt=0, description="Multiplier for premium products")
    standard_multiplier: float = Field(1.5, gt=0, description="Multiplier for standard products")
    basic_multiplier: float = Field(1.2, gt=0, description="Multiplier for basic products")

class DiscountRulesRequest(BaseModel):
    bulk_threshold: int = Field(100, gt=0, description="Minimum quantity for bulk discount")
    bulk_discount: float = Field(0.1, ge=0, le=1, description="Bulk discount rate")
    medium_threshold: int = Field(50, gt=0, description="Minimum quantity for medium discount")
    medium_discount: float = Field(0.05, ge=0, le=1, description="Medium discount rate")

class PricingRequest(BaseModel):
    products: List[ProductRequest] = Field(..., description="List of products to price")
    pricing_rules: Optional[PricingRulesRequest] = Field(default_factory=PricingRulesRequest)
    discount_rules: Optional[DiscountRulesRequest] = Field(default_factory=DiscountRulesRequest)

class PricingResponse(BaseModel):
    success: bool
    message: str
    summary: Optional[Dict[str, Any]] = None
    products: Optional[List[Dict[str, Any]]] = None

class RARoCPricingResponse(BaseModel):
    success: bool
    message: str
    summary: Dict[str, Any]
    borrowers: List[Dict[str, Any]]
    model_info: Dict[str, str]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting PricingEngine API")
    yield
    logger.info("Shutting down PricingEngine API")
    spark_manager.stop()


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="A high-performance pricing engine using PySpark for data processing with RAROC-based risk pricing",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pricing engines
pricing_engine = PricingEngine()
raroc_pricing_engine = RARoCPricingEngine()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "spark_session": "active"}


@app.post("/pricing/calculate", response_model=PricingResponse)
async def calculate_pricing(request: PricingRequest):
    """
    Calculate pricing for a list of products using PySpark.
    
    This endpoint processes product data through the pricing engine
    to calculate base prices and apply discounts.
    """
    try:
        # Convert request to Spark DataFrame
        products_data = [product.dict() for product in request.products]
        products_df = pricing_engine.spark.createDataFrame(products_data)
        
        # Calculate base prices
        pricing_rules = request.pricing_rules.dict() if request.pricing_rules else {}
        prices_df = pricing_engine.calculate_base_price(products_df, pricing_rules)
        
        # Apply discounts
        discount_rules = request.discount_rules.dict() if request.discount_rules else {}
        final_prices_df = pricing_engine.apply_discounts(prices_df, discount_rules)
        
        # Calculate summary
        summary = pricing_engine.calculate_pricing_summary(final_prices_df)
        
        # Collect results
        results = final_prices_df.collect()
        products_result = [row.asDict() for row in results]
        
        return PricingResponse(
            success=True,
            message=f"Successfully calculated pricing for {len(products_result)} products",
            summary=summary,
            products=products_result
        )
        
    except Exception as e:
        logger.error(f"Error calculating pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pricing calculation failed: {str(e)}")


@app.get("/pricing/sample")
async def get_sample_pricing():
    """
    Get sample pricing calculation using demo data.
    
    This endpoint demonstrates the pricing engine with sample product data.
    """
    try:
        # Create sample data
        sample_df = pricing_engine.create_sample_data()
        
        # Default rules
        pricing_rules = {"premium_multiplier": 2.0, "standard_multiplier": 1.5, "basic_multiplier": 1.2}
        discount_rules = {"bulk_threshold": 100, "bulk_discount": 0.1, "medium_threshold": 50, "medium_discount": 0.05}
        
        # Calculate pricing
        prices_df = pricing_engine.calculate_base_price(sample_df, pricing_rules)
        final_prices_df = pricing_engine.apply_discounts(prices_df, discount_rules)
        
        # Get summary and results
        summary = pricing_engine.calculate_pricing_summary(final_prices_df)
        results = final_prices_df.collect()
        products_result = [row.asDict() for row in results]
        
        return PricingResponse(
            success=True,
            message="Sample pricing calculation completed",
            summary=summary,
            products=products_result
        )
        
    except Exception as e:
        logger.error(f"Error with sample pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sample pricing failed: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """Get basic application metrics."""
    return {
        "spark_app_name": settings.spark_app_name,
        "spark_master": settings.spark_master,
        "api_version": settings.version,
        "debug_mode": settings.debug
    }


@app.post("/raroc/calculate", response_model=RARoCPricingResponse)
async def calculate_raroc_pricing(request: RARoCPricingRequest):
    """
    Calculate RAROC-based pricing for borrowers using PD/LGD models.
    
    This endpoint processes borrower data through sophisticated risk models
    to calculate risk-adjusted return on capital and minimum pricing.
    """
    try:
        # Convert request to Spark DataFrame
        borrowers_data = [borrower.dict() for borrower in request.borrowers]
        borrowers_df = raroc_pricing_engine.spark.createDataFrame(borrowers_data)
        
        # Prepare features for risk calculation
        features = {
            'risk_type': request.risk_type,
            'target_raroc': request.target_raroc,
            'competitive_margin': request.competitive_margin,
            'stress_pd_factor': request.stress_pd_factor,
            'stress_lgd_factor': request.stress_lgd_factor,
            'economic_condition': request.economic_condition
        }
        
        # Calculate RAROC pricing
        result_df, summary = raroc_pricing_engine.calculate_risk_based_pricing(
            borrowers_df, request.pd_model, request.lgd_model, features
        )
        
        # Collect results
        results = result_df.collect()
        borrowers_result = [row.asDict() for row in results]
        
        return RARoCPricingResponse(
            success=True,
            message=f"Successfully calculated RAROC pricing for {len(borrowers_result)} borrowers",
            summary=summary,
            borrowers=borrowers_result,
            model_info={
                "pd_model": request.pd_model,
                "lgd_model": request.lgd_model,
                "risk_type": request.risk_type
            }
        )
        
    except Exception as e:
        logger.error(f"Error calculating RAROC pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAROC pricing calculation failed: {str(e)}")


@app.get("/raroc/sample")
async def get_sample_raroc_pricing():
    """
    Get sample RAROC pricing calculation using demo portfolio data.
    
    This endpoint demonstrates the RAROC pricing engine with sample borrower data.
    """
    try:
        # Create sample portfolio
        sample_df = raroc_pricing_engine.create_sample_portfolio()
        
        # Default parameters
        features = {
            'risk_type': 'corporate',
            'target_raroc': 0.15,
            'competitive_margin': 0.02,
            'economic_condition': 'normal'
        }
        
        # Calculate RAROC pricing
        result_df, summary = raroc_pricing_engine.calculate_risk_based_pricing(
            sample_df, 'logistic', 'hybrid', features
        )
        
        # Get results
        results = result_df.collect()
        borrowers_result = [row.asDict() for row in results]
        
        return RARoCPricingResponse(
            success=True,
            message="Sample RAROC pricing calculation completed",
            summary=summary,
            borrowers=borrowers_result,
            model_info={
                "pd_model": "logistic",
                "lgd_model": "hybrid",
                "risk_type": "corporate"
            }
        )
        
    except Exception as e:
        logger.error(f"Error with sample RAROC pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sample RAROC pricing failed: {str(e)}")


@app.post("/raroc/benchmark")
async def benchmark_raroc_models(borrowers: List[BorrowerRequest]):
    """
    Benchmark different PD/LGD model combinations for the same portfolio.
    
    This endpoint compares the performance of different risk model combinations.
    """
    try:
        # Convert to DataFrame
        borrowers_data = [borrower.dict() for borrower in borrowers]
        borrowers_df = raroc_pricing_engine.spark.createDataFrame(borrowers_data)
        
        # Benchmark models
        benchmark_results = raroc_pricing_engine.benchmark_pricing_models(borrowers_df)
        
        return {
            "success": True,
            "message": f"Benchmarked models for {len(borrowers)} borrowers",
            "benchmark_results": benchmark_results,
            "models_compared": list(benchmark_results.keys())
        }
        
    except Exception as e:
        logger.error(f"Error benchmarking RAROC models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model benchmarking failed: {str(e)}")


@app.get("/raroc/models")
async def get_available_models():
    """Get information about available PD and LGD models."""
    return {
        "pd_models": {
            "logistic": "Logistic regression-based PD model with multiple risk factors",
            "score_based": "Credit score-based PD model with rating buckets", 
            "industry": "Industry-specific PD model with sector risk factors"
        },
        "lgd_models": {
            "collateral": "Collateral-based LGD model with recovery rates by asset type",
            "industry": "Industry-based LGD model with sector recovery characteristics",
            "hybrid": "Hybrid model combining collateral and industry factors"
        },
        "risk_types": ["corporate", "sme", "retail", "sovereign", "bank"],
        "economic_conditions": ["recession", "normal", "expansion"]
    }
