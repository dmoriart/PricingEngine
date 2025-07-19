from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
from contextlib import asynccontextmanager

from config.settings import settings
from pricing.engine import PricingEngine
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
    description="A high-performance pricing engine using PySpark for data processing",
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

# Initialize pricing engine
pricing_engine = PricingEngine()


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
