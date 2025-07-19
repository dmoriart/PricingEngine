from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lit, sum as spark_sum, avg, max as spark_max, min as spark_min
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
from decimal import Decimal
from typing import Dict, List, Any, Optional
import logging
from core.spark_manager import spark_manager

logger = logging.getLogger(__name__)


class PricingEngine:
    """Main pricing engine for calculating prices using PySpark."""
    
    def __init__(self):
        self.spark = spark_manager.spark
    
    def calculate_base_price(self, products_df: DataFrame, pricing_rules: Dict[str, Any]) -> DataFrame:
        """
        Calculate base prices for products using configured rules.
        
        Args:
            products_df: DataFrame with product information
            pricing_rules: Dictionary containing pricing rules and parameters
            
        Returns:
            DataFrame with calculated base prices
        """
        try:
            # Apply base pricing logic
            result_df = products_df.withColumn(
                "base_price",
                when(col("category") == "premium", col("cost") * lit(pricing_rules.get("premium_multiplier", 2.0)))
                .when(col("category") == "standard", col("cost") * lit(pricing_rules.get("standard_multiplier", 1.5)))
                .otherwise(col("cost") * lit(pricing_rules.get("basic_multiplier", 1.2)))
            )
            
            logger.info(f"Calculated base prices for {result_df.count()} products")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating base prices: {str(e)}")
            raise
    
    def apply_discounts(self, prices_df: DataFrame, discount_rules: Dict[str, Any]) -> DataFrame:
        """
        Apply discount rules to calculated prices.
        
        Args:
            prices_df: DataFrame with base prices
            discount_rules: Dictionary containing discount rules
            
        Returns:
            DataFrame with discounted prices
        """
        try:
            # Apply volume discounts
            result_df = prices_df.withColumn(
                "discount_rate",
                when(col("quantity") >= discount_rules.get("bulk_threshold", 100), 
                     lit(discount_rules.get("bulk_discount", 0.1)))
                .when(col("quantity") >= discount_rules.get("medium_threshold", 50), 
                     lit(discount_rules.get("medium_discount", 0.05)))
                .otherwise(lit(0.0))
            ).withColumn(
                "final_price",
                col("base_price") * (lit(1.0) - col("discount_rate"))
            )
            
            logger.info(f"Applied discounts to {result_df.count()} products")
            return result_df
            
        except Exception as e:
            logger.error(f"Error applying discounts: {str(e)}")
            raise
    
    def calculate_pricing_summary(self, prices_df: DataFrame) -> Dict[str, Any]:
        """
        Calculate pricing summary statistics.
        
        Args:
            prices_df: DataFrame with final prices
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            summary = prices_df.agg(
                spark_sum("final_price").alias("total_revenue"),
                avg("final_price").alias("avg_price"),
                spark_max("final_price").alias("max_price"),
                spark_min("final_price").alias("min_price"),
                spark_sum("quantity").alias("total_quantity")
            ).collect()[0]
            
            return {
                "total_revenue": float(summary.total_revenue or 0),
                "average_price": float(summary.avg_price or 0),
                "max_price": float(summary.max_price or 0),
                "min_price": float(summary.min_price or 0),
                "total_quantity": int(summary.total_quantity or 0),
                "total_products": prices_df.count()
            }
            
        except Exception as e:
            logger.error(f"Error calculating pricing summary: {str(e)}")
            raise
    
    def create_sample_data(self) -> DataFrame:
        """Create sample product data for testing."""
        try:
            schema = StructType([
                StructField("product_id", StringType(), True),
                StructField("name", StringType(), True),
                StructField("category", StringType(), True),
                StructField("cost", DoubleType(), True),
                StructField("quantity", IntegerType(), True)
            ])
            
            sample_data = [
                ("P001", "Premium Widget", "premium", 100.0, 150),
                ("P002", "Standard Widget", "standard", 75.0, 75),
                ("P003", "Basic Widget", "basic", 50.0, 25),
                ("P004", "Deluxe Widget", "premium", 120.0, 200),
                ("P005", "Economy Widget", "basic", 30.0, 300)
            ]
            
            return self.spark.createDataFrame(sample_data, schema)
            
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            raise
