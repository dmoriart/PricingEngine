from typing import Dict, Any, Optional, List
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit, when, greatest, least
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
import logging

from core.spark_manager import spark_manager
from risk.pd_models import LogisticPDModel, ScoreBasedPDModel, IndustryPDModel
from risk.lgd_models import CollateralBasedLGDModel, IndustryLGDModel, HybridLGDModel
from risk.raroc_calculator import RARoCCalculator

logger = logging.getLogger(__name__)


class RARoCPricingEngine:
    """
    Advanced pricing engine using Risk-Adjusted Return on Capital (RAROC) methodology.
    
    This engine calculates risk-based pricing by:
    1. Estimating Probability of Default (PD)
    2. Calculating Loss Given Default (LGD)
    3. Determining Exposure at Default (EAD)
    4. Computing RAROC and minimum pricing
    """
    
    def __init__(self):
        """Initialize RAROC pricing engine with risk models."""
        self.spark = spark_manager.spark
        
        # Initialize risk models
        self.pd_models = {
            'logistic': LogisticPDModel(),
            'score_based': ScoreBasedPDModel(),
            'industry': IndustryPDModel()
        }
        
        self.lgd_models = {
            'collateral': CollateralBasedLGDModel(),
            'industry': IndustryLGDModel(),
            'hybrid': HybridLGDModel()
        }
        
        self.raroc_calculator = RARoCCalculator()
    
    def calculate_risk_based_pricing(self, 
                                   borrowers_df: DataFrame,
                                   pd_model: str = 'logistic',
                                   lgd_model: str = 'hybrid',
                                   features: Optional[Dict[str, Any]] = None) -> DataFrame:
        """
        Calculate comprehensive risk-based pricing using RAROC methodology.
        
        Args:
            borrowers_df: DataFrame with borrower and loan information
            pd_model: PD model to use ('logistic', 'score_based', 'industry')
            lgd_model: LGD model to use ('collateral', 'industry', 'hybrid')
            features: Additional features and parameters
            
        Returns:
            DataFrame with complete pricing analysis
        """
        try:
            features = features or {}
            
            # Step 1: Calculate Probability of Default
            logger.info(f"Calculating PD using {pd_model} model")
            if pd_model not in self.pd_models:
                raise ValueError(f"Unknown PD model: {pd_model}")
            
            result_df = self.pd_models[pd_model].calculate_pd(borrowers_df, features)
            
            # Step 2: Calculate Loss Given Default
            logger.info(f"Calculating LGD using {lgd_model} model")
            if lgd_model not in self.lgd_models:
                raise ValueError(f"Unknown LGD model: {lgd_model}")
            
            result_df = self.lgd_models[lgd_model].calculate_lgd(result_df, features)
            
            # Step 3: Calculate RAROC and pricing
            logger.info("Calculating RAROC and minimum pricing")
            result_df = self.raroc_calculator.calculate_raroc(result_df, features)
            result_df = self.raroc_calculator.calculate_minimum_price(result_df, features)
            
            # Step 4: Add pricing recommendations
            result_df = self._add_pricing_recommendations(result_df, features)
            
            # Step 5: Calculate pricing summary
            summary = self._calculate_pricing_summary(result_df)
            
            logger.info(f"Completed risk-based pricing for {result_df.count()} borrowers")
            return result_df, summary
            
        except Exception as e:
            logger.error(f"Error in risk-based pricing calculation: {str(e)}")
            raise
    
    def _add_pricing_recommendations(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """Add pricing recommendations and risk classifications."""
        try:
            # Classify risk levels based on PD
            df = df.withColumn(
                'risk_rating',
                when(col('pd_score') <= 0.01, 'AAA')
                .when(col('pd_score') <= 0.02, 'AA')
                .when(col('pd_score') <= 0.05, 'A')
                .when(col('pd_score') <= 0.10, 'BBB')
                .when(col('pd_score') <= 0.20, 'BB')
                .when(col('pd_score') <= 0.30, 'B')
                .otherwise('CCC')
            )
            
            # Pricing recommendations based on RAROC
            target_raroc = features.get('target_raroc', 0.15)
            
            df = df.withColumn(
                'pricing_recommendation',
                when(col('raroc') >= target_raroc * 1.5, 'HIGHLY_ATTRACTIVE')
                .when(col('raroc') >= target_raroc, 'ATTRACTIVE')
                .when(col('raroc') >= target_raroc * 0.8, 'ACCEPTABLE')
                .when(col('raroc') >= target_raroc * 0.5, 'MARGINAL')
                .otherwise('REJECT')
            )
            
            # Calculate competitive pricing (minimum rate + margin)
            competitive_margin = features.get('competitive_margin', 0.02)  # 2% margin
            df = df.withColumn(
                'competitive_rate',
                col('minimum_rate') + lit(competitive_margin)
            )
            
            # Calculate stress test pricing (adverse scenario)
            stress_pd_factor = features.get('stress_pd_factor', 2.0)  # 2x PD in stress
            stress_lgd_factor = features.get('stress_lgd_factor', 1.3)  # 1.3x LGD in stress
            
            df = df.withColumn(
                'stress_expected_loss',
                col('pd_score') * lit(stress_pd_factor) * 
                col('lgd_score') * lit(stress_lgd_factor) * col('ead_amount')
            ).withColumn(
                'stress_minimum_rate',
                (col('stress_expected_loss') + col('funding_cost') + 
                 col('operational_cost') + 
                 (col('economic_capital') * lit(0.15))) / col('ead_amount')
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding pricing recommendations: {str(e)}")
            raise
    
    def _calculate_pricing_summary(self, df: DataFrame) -> Dict[str, Any]:
        """Calculate portfolio-level pricing summary statistics."""
        try:
            # Collect summary statistics
            summary_data = df.agg({
                'ead_amount': 'sum',
                'expected_loss': 'sum',
                'economic_capital': 'sum',
                'net_income': 'sum',
                'pd_score': 'avg',
                'lgd_score': 'avg',
                'raroc': 'avg',
                'minimum_rate': 'avg'
            }).collect()[0]
            
            # Calculate portfolio RAROC
            total_capital = float(summary_data['sum(economic_capital)'] or 0)
            total_income = float(summary_data['sum(net_income)'] or 0)
            portfolio_raroc = total_income / total_capital if total_capital > 0 else 0
            
            # Count by risk rating
            risk_counts = df.groupBy('risk_rating').count().collect()
            risk_distribution = {row.risk_rating: row.count for row in risk_counts}
            
            # Count by pricing recommendation
            pricing_counts = df.groupBy('pricing_recommendation').count().collect()
            pricing_distribution = {row.pricing_recommendation: row.count for row in pricing_counts}
            
            return {
                'total_exposure': float(summary_data['sum(ead_amount)'] or 0),
                'total_expected_loss': float(summary_data['sum(expected_loss)'] or 0),
                'total_economic_capital': total_capital,
                'total_net_income': total_income,
                'portfolio_raroc': portfolio_raroc,
                'average_pd': float(summary_data['avg(pd_score)'] or 0),
                'average_lgd': float(summary_data['avg(lgd_score)'] or 0),
                'average_individual_raroc': float(summary_data['avg(raroc)'] or 0),
                'average_minimum_rate': float(summary_data['avg(minimum_rate)'] or 0),
                'expected_loss_rate': (float(summary_data['sum(expected_loss)'] or 0) / 
                                     float(summary_data['sum(ead_amount)'] or 1)),
                'risk_distribution': risk_distribution,
                'pricing_recommendation_distribution': pricing_distribution
            }
            
        except Exception as e:
            logger.error(f"Error calculating pricing summary: {str(e)}")
            raise
    
    def create_sample_portfolio(self) -> DataFrame:
        """Create sample portfolio data for testing and demonstration."""
        try:
            schema = StructType([
                StructField("borrower_id", StringType(), True),
                StructField("borrower_name", StringType(), True),
                StructField("credit_score", IntegerType(), True),
                StructField("debt_to_income", DoubleType(), True),
                StructField("loan_to_value", DoubleType(), True),
                StructField("employment_years", IntegerType(), True),
                StructField("payment_history_score", IntegerType(), True),
                StructField("industry", StringType(), True),
                StructField("company_size", StringType(), True),
                StructField("collateral_type", StringType(), True),
                StructField("seniority", StringType(), True),
                StructField("facility_type", StringType(), True),
                StructField("exposure_amount", DoubleType(), True),
                StructField("outstanding_amount", DoubleType(), True),
                StructField("undrawn_amount", DoubleType(), True),
                StructField("loan_term", IntegerType(), True),
                StructField("region", StringType(), True)
            ])
            
            sample_data = [
                ("B001", "TechCorp Inc", 750, 0.35, 0.75, 8, 95, "technology", "large", 
                 "equipment", "senior_secured", "term_loan", 5000000.0, 5000000.0, 0.0, 5, "developed"),
                ("B002", "Manufacturing LLC", 680, 0.45, 0.80, 12, 85, "manufacturing", "medium",
                 "real_estate", "senior_secured", "revolving_credit", 2000000.0, 1500000.0, 500000.0, 3, "developed"),
                ("B003", "Retail Chain", 620, 0.55, 0.85, 5, 75, "retail", "large",
                 "inventory", "senior_unsecured", "term_loan", 3000000.0, 3000000.0, 0.0, 7, "developed"),
                ("B004", "Healthcare Services", 720, 0.40, 0.70, 10, 90, "healthcare", "medium",
                 "equipment", "senior_secured", "revolving_credit", 1500000.0, 1000000.0, 500000.0, 5, "developed"),
                ("B005", "Energy Company", 700, 0.50, 0.75, 15, 80, "energy", "large",
                 "real_estate", "senior_secured", "term_loan", 10000000.0, 10000000.0, 0.0, 10, "developed"),
                ("B006", "Small Restaurant", 580, 0.65, 0.90, 3, 65, "hospitality", "small",
                 "personal_guarantee", "subordinated", "term_loan", 500000.0, 500000.0, 0.0, 5, "developed"),
                ("B007", "Software Startup", 650, 0.40, 0.60, 2, 70, "technology", "small",
                 "unsecured", "senior_unsecured", "revolving_credit", 1000000.0, 250000.0, 750000.0, 3, "developed"),
                ("B008", "Real Estate Developer", 690, 0.60, 0.80, 20, 85, "real_estate", "medium",
                 "real_estate", "senior_secured", "term_loan", 8000000.0, 8000000.0, 0.0, 15, "developed")
            ]
            
            return self.spark.createDataFrame(sample_data, schema)
            
        except Exception as e:
            logger.error(f"Error creating sample portfolio: {str(e)}")
            raise
    
    def benchmark_pricing_models(self, df: DataFrame) -> Dict[str, Any]:
        """Benchmark different PD and LGD model combinations."""
        try:
            results = {}
            
            for pd_model_name in self.pd_models.keys():
                for lgd_model_name in self.lgd_models.keys():
                    model_key = f"{pd_model_name}_{lgd_model_name}"
                    
                    # Calculate pricing with this model combination
                    result_df, summary = self.calculate_risk_based_pricing(
                        df, pd_model_name, lgd_model_name
                    )
                    
                    results[model_key] = {
                        'portfolio_raroc': summary['portfolio_raroc'],
                        'average_minimum_rate': summary['average_minimum_rate'],
                        'expected_loss_rate': summary['expected_loss_rate'],
                        'total_economic_capital': summary['total_economic_capital']
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error benchmarking pricing models: {str(e)}")
            raise
