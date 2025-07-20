from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lit, exp, log, sqrt
from pyspark.sql.types import DoubleType
import logging

logger = logging.getLogger(__name__)


class PDModel(ABC):
    """Abstract base class for Probability of Default models."""
    
    @abstractmethod
    def calculate_pd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """Calculate probability of default for given features."""
        pass


class LogisticPDModel(PDModel):
    """Logistic regression-based PD model."""
    
    def __init__(self, coefficients: Optional[Dict[str, float]] = None):
        """
        Initialize logistic PD model.
        
        Args:
            coefficients: Model coefficients for features
        """
        # Default coefficients (these would normally come from model training)
        self.coefficients = coefficients or {
            'intercept': -2.5,
            'credit_score': -0.008,      # Higher score = lower PD
            'debt_to_income': 1.2,       # Higher DTI = higher PD
            'loan_to_value': 0.5,        # Higher LTV = higher PD
            'employment_years': -0.1,     # More years = lower PD
            'payment_history_score': -0.02  # Better history = lower PD
        }
    
    def calculate_pd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """
        Calculate PD using logistic regression.
        
        PD = 1 / (1 + exp(-(intercept + β1*X1 + β2*X2 + ...)))
        """
        try:
            # Get column names safely
            column_names = df.columns
            
            # Build linear combination
            linear_combination = lit(self.coefficients['intercept'])
            
            for feature, coeff in self.coefficients.items():
                if feature != 'intercept' and feature in column_names:
                    linear_combination = linear_combination + (col(feature) * lit(coeff))
            
            # Apply logistic function: PD = 1 / (1 + exp(-linear_combination))
            result_df = df.withColumn(
                'pd_score',
                lit(1.0) / (lit(1.0) + exp(-linear_combination))
            ).withColumn(
                'pd_score',
                when(col('pd_score') > 0.99, 0.99)
                .when(col('pd_score') < 0.001, 0.001)
                .otherwise(col('pd_score'))
            )
            
            logger.info(f"Calculated PD for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating PD: {str(e)}")
            raise


class ScoreBasedPDModel(PDModel):
    """Credit score-based PD model with rating buckets."""
    
    def __init__(self):
        """Initialize score-based PD model with rating mapping."""
        # Credit score to PD mapping (these would be calibrated from historical data)
        self.score_to_pd = {
            800: 0.002,   # Excellent
            750: 0.005,   # Very Good
            700: 0.015,   # Good
            650: 0.035,   # Fair
            600: 0.075,   # Poor
            550: 0.150,   # Very Poor
            500: 0.250,   # Default bucket
        }
    
    def calculate_pd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """Calculate PD based on credit score ranges."""
        try:
            # Get column names safely
            column_names = df.columns
            
            result_df = df
            
            # Apply PD based on credit score buckets
            pd_condition = when(col('credit_score') >= 800, lit(0.002)) \
                .when(col('credit_score') >= 750, lit(0.005)) \
                .when(col('credit_score') >= 700, lit(0.015)) \
                .when(col('credit_score') >= 650, lit(0.035)) \
                .when(col('credit_score') >= 600, lit(0.075)) \
                .when(col('credit_score') >= 550, lit(0.150)) \
                .otherwise(lit(0.250))
            
            result_df = result_df.withColumn('pd_score', pd_condition)
            
            # Apply adjustments based on other factors if available
            if 'debt_to_income' in column_names:
                result_df = result_df.withColumn(
                    'pd_score',
                    when(col('debt_to_income') > 0.5, col('pd_score') * lit(1.5))
                    .when(col('debt_to_income') > 0.4, col('pd_score') * lit(1.2))
                    .otherwise(col('pd_score'))
                )
            
            logger.info(f"Calculated score-based PD for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating score-based PD: {str(e)}")
            raise


class IndustryPDModel(PDModel):
    """Industry-specific PD model."""
    
    def __init__(self):
        """Initialize industry PD model with sector-specific rates."""
        # Industry base PD rates (would be calibrated from historical data)
        self.industry_pd = {
            'technology': 0.015,
            'healthcare': 0.020,
            'financial_services': 0.025,
            'manufacturing': 0.035,
            'retail': 0.045,
            'energy': 0.055,
            'real_estate': 0.065,
            'hospitality': 0.080,
            'default': 0.040
        }
    
    def calculate_pd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """Calculate PD based on industry sector."""
        try:
            # Get column names safely
            column_names = df.columns
            
            # Build industry-based PD mapping
            industry_condition = lit(self.industry_pd['default'])
            
            for industry, pd_rate in self.industry_pd.items():
                if industry != 'default':
                    industry_condition = when(
                        col('industry') == industry, lit(pd_rate)
                    ).otherwise(industry_condition)
            
            result_df = df.withColumn('pd_score', industry_condition)
            
            # Apply size adjustments if available
            if 'company_size' in column_names:
                result_df = result_df.withColumn(
                    'pd_score',
                    when(col('company_size') == 'large', col('pd_score') * lit(0.8))
                    .when(col('company_size') == 'medium', col('pd_score') * lit(0.9))
                    .when(col('company_size') == 'small', col('pd_score') * lit(1.2))
                    .otherwise(col('pd_score'))
                )
            
            logger.info(f"Calculated industry-based PD for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating industry PD: {str(e)}")
            raise
