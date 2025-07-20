from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lit, greatest, least
import logging

logger = logging.getLogger(__name__)


class LGDModel(ABC):
    """Abstract base class for Loss Given Default models."""
    
    @abstractmethod
    def calculate_lgd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """Calculate loss given default for given features."""
        pass


class CollateralBasedLGDModel(LGDModel):
    """LGD model based on collateral type and coverage."""
    
    def __init__(self):
        """Initialize collateral-based LGD model."""
        # Base LGD rates by collateral type (from historical recovery data)
        self.base_lgd = {
            'real_estate': 0.25,      # Strong collateral
            'equipment': 0.45,        # Moderate collateral
            'inventory': 0.65,        # Weak collateral
            'accounts_receivable': 0.55,
            'cash_securities': 0.05,  # Very strong
            'personal_guarantee': 0.75,
            'unsecured': 0.85,        # Highest LGD
            'default': 0.70
        }
        
        # Recovery rate adjustments based on economic conditions
        self.economic_adjustments = {
            'recession': 1.3,         # Higher LGD in recession
            'normal': 1.0,
            'expansion': 0.9          # Lower LGD in good times
        }
    
    def calculate_lgd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """
        Calculate LGD based on collateral type and loan-to-value ratio.
        
        LGD = Base_LGD × LTV_Adjustment × Economic_Adjustment × Seniority_Adjustment
        """
        try:
            # Get column names safely
            column_names = df.columns
            
            # Start with base LGD by collateral type
            lgd_condition = lit(self.base_lgd['default'])
            
            for collateral_type, base_rate in self.base_lgd.items():
                if collateral_type != 'default':
                    lgd_condition = when(
                        col('collateral_type') == collateral_type, lit(base_rate)
                    ).otherwise(lgd_condition)
            
            result_df = df.withColumn('base_lgd', lgd_condition)
            
            # Apply LTV adjustment if available
            if 'loan_to_value' in column_names:
                # Higher LTV = Higher LGD (less collateral coverage)
                result_df = result_df.withColumn(
                    'ltv_adjustment',
                    when(col('loan_to_value') <= 0.5, lit(0.8))    # Strong coverage
                    .when(col('loan_to_value') <= 0.7, lit(0.9))   # Good coverage
                    .when(col('loan_to_value') <= 0.8, lit(1.0))   # Fair coverage
                    .when(col('loan_to_value') <= 0.9, lit(1.2))   # Weak coverage
                    .otherwise(lit(1.4))                           # Very weak coverage
                )
            else:
                result_df = result_df.withColumn('ltv_adjustment', lit(1.0))
            
            # Apply seniority adjustment
            if 'seniority' in column_names:
                result_df = result_df.withColumn(
                    'seniority_adjustment',
                    when(col('seniority') == 'senior_secured', lit(0.8))
                    .when(col('seniority') == 'senior_unsecured', lit(1.0))
                    .when(col('seniority') == 'subordinated', lit(1.3))
                    .otherwise(lit(1.0))
                )
            else:
                result_df = result_df.withColumn('seniority_adjustment', lit(1.0))
            
            # Apply economic condition adjustment
            economic_factor = features.get('economic_condition', 'normal')
            econ_adjustment = self.economic_adjustments.get(economic_factor, 1.0)
            
            # Calculate final LGD
            result_df = result_df.withColumn(
                'lgd_score',
                least(
                    col('base_lgd') * col('ltv_adjustment') * 
                    col('seniority_adjustment') * lit(econ_adjustment),
                    lit(0.95)  # Cap at 95%
                )
            ).withColumn(
                'lgd_score',
                greatest(col('lgd_score'), lit(0.05))  # Floor at 5%
            )
            
            logger.info(f"Calculated collateral-based LGD for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating collateral-based LGD: {str(e)}")
            raise


class IndustryLGDModel(LGDModel):
    """LGD model based on industry characteristics."""
    
    def __init__(self):
        """Initialize industry-based LGD model."""
        # Industry-specific LGD rates based on asset tangibility and market liquidity
        self.industry_lgd = {
            'real_estate': 0.30,      # Tangible assets
            'manufacturing': 0.40,    # Equipment and inventory
            'energy': 0.35,           # Infrastructure assets
            'transportation': 0.45,   # Specialized equipment
            'technology': 0.70,       # Mostly intangible assets
            'services': 0.75,         # Limited tangible assets
            'healthcare': 0.50,       # Mixed asset base
            'retail': 0.60,           # Inventory and fixtures
            'financial_services': 0.65,
            'hospitality': 0.55,      # Real estate + equipment
            'default': 0.60
        }
    
    def calculate_lgd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """Calculate LGD based on industry sector."""
        try:
            # Get column names safely
            column_names = df.columns
            
            # Build industry-based LGD mapping
            industry_condition = lit(self.industry_lgd['default'])
            
            for industry, lgd_rate in self.industry_lgd.items():
                if industry != 'default':
                    industry_condition = when(
                        col('industry') == industry, lit(lgd_rate)
                    ).otherwise(industry_condition)
            
            result_df = df.withColumn('lgd_score', industry_condition)
            
            # Apply company size adjustments (larger companies typically have better recovery)
            if 'company_size' in column_names:
                result_df = result_df.withColumn(
                    'lgd_score',
                    when(col('company_size') == 'large', col('lgd_score') * lit(0.85))
                    .when(col('company_size') == 'medium', col('lgd_score') * lit(0.95))
                    .when(col('company_size') == 'small', col('lgd_score') * lit(1.1))
                    .otherwise(col('lgd_score'))
                )
            
            # Apply geographic adjustments if available
            if 'region' in column_names:
                result_df = result_df.withColumn(
                    'lgd_score',
                    when(col('region') == 'developed', col('lgd_score') * lit(0.9))
                    .when(col('region') == 'emerging', col('lgd_score') * lit(1.2))
                    .otherwise(col('lgd_score'))
                )
            
            # Ensure LGD stays within reasonable bounds
            result_df = result_df.withColumn(
                'lgd_score',
                least(greatest(col('lgd_score'), lit(0.05)), lit(0.95))
            )
            
            logger.info(f"Calculated industry-based LGD for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating industry LGD: {str(e)}")
            raise


class HybridLGDModel(LGDModel):
    """Hybrid LGD model combining multiple factors."""
    
    def __init__(self):
        """Initialize hybrid LGD model."""
        self.collateral_model = CollateralBasedLGDModel()
        self.industry_model = IndustryLGDModel()
        
        # Weights for combining different models
        self.model_weights = {
            'collateral': 0.6,
            'industry': 0.4
        }
    
    def calculate_lgd(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """Calculate LGD using weighted combination of models."""
        try:
            # Get column names safely
            column_names = df.columns
            
            # Calculate LGD using both models
            collateral_df = self.collateral_model.calculate_lgd(df, features)
            industry_df = self.industry_model.calculate_lgd(df, features)
            
            # Combine the models with weights
            result_df = collateral_df.withColumn(
                'collateral_lgd', col('lgd_score')
            ).join(
                industry_df.select('lgd_score').withColumnRenamed('lgd_score', 'industry_lgd'),
                how='inner'
            ).withColumn(
                'lgd_score',
                (col('collateral_lgd') * lit(self.model_weights['collateral'])) +
                (col('industry_lgd') * lit(self.model_weights['industry']))
            )
            
            # Apply final adjustments based on loan characteristics
            if 'loan_term' in column_names:
                # Longer term loans typically have higher LGD
                result_df = result_df.withColumn(
                    'lgd_score',
                    when(col('loan_term') > 5, col('lgd_score') * lit(1.1))
                    .when(col('loan_term') > 3, col('lgd_score') * lit(1.05))
                    .otherwise(col('lgd_score'))
                )
            
            # Ensure final bounds
            result_df = result_df.withColumn(
                'lgd_score',
                least(greatest(col('lgd_score'), lit(0.05)), lit(0.95))
            )
            
            logger.info(f"Calculated hybrid LGD for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating hybrid LGD: {str(e)}")
            raise
