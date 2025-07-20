from typing import Dict, Any, Optional
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit, when, greatest, least, log
import logging

logger = logging.getLogger(__name__)


class EADModel:
    """Exposure at Default model for calculating potential exposure."""
    
    def __init__(self):
        """Initialize EAD model with conversion factors."""
        # Credit conversion factors by facility type
        self.ccf_rates = {
            'term_loan': 1.0,         # Fully drawn
            'revolving_credit': 0.75,  # Partially drawn on average
            'letter_of_credit': 0.5,   # Contingent exposure
            'guarantee': 1.0,          # Full exposure if called
            'commitment': 0.3,         # Low probability of draw
            'default': 0.75
        }
    
    def calculate_ead(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """
        Calculate Exposure at Default.
        
        EAD = Outstanding_Amount + (Undrawn_Amount × CCF)
        """
        try:
            # Apply credit conversion factors by facility type
            ccf_condition = lit(self.ccf_rates['default'])
            
            for facility_type, ccf in self.ccf_rates.items():
                if facility_type != 'default':
                    ccf_condition = when(
                        col('facility_type') == facility_type, lit(ccf)
                    ).otherwise(ccf_condition)
            
            result_df = df.withColumn('ccf', ccf_condition)
            
            # Calculate EAD
            if 'outstanding_amount' in [c.name for c in df.columns] and \
               'undrawn_amount' in [c.name for c in df.columns]:
                result_df = result_df.withColumn(
                    'ead_amount',
                    col('outstanding_amount') + (col('undrawn_amount') * col('ccf'))
                )
            else:
                # If detailed amounts not available, use total limit
                result_df = result_df.withColumn(
                    'ead_amount',
                    col('exposure_amount') * col('ccf')
                )
            
            # Apply stress scenarios if specified
            stress_factor = features.get('stress_factor', 1.0)
            result_df = result_df.withColumn(
                'ead_amount',
                col('ead_amount') * lit(stress_factor)
            )
            
            logger.info(f"Calculated EAD for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating EAD: {str(e)}")
            raise


class CapitalModel:
    """Capital allocation model for RAROC calculations."""
    
    def __init__(self):
        """Initialize capital model with regulatory and economic capital factors."""
        # Regulatory capital requirements by risk type
        self.regulatory_capital_rates = {
            'corporate': 0.08,        # 8% for standard corporate
            'sme': 0.075,            # 7.5% for SME
            'retail': 0.035,         # 3.5% for retail
            'sovereign': 0.0,        # 0% for AAA sovereign
            'bank': 0.02,            # 2% for investment grade banks
            'default': 0.08
        }
        
        # Economic capital multipliers (typically higher than regulatory)
        self.economic_capital_multiplier = 1.5
    
    def calculate_capital(self, df: DataFrame, risk_type: str = 'corporate') -> DataFrame:
        """
        Calculate required capital for RAROC.
        
        Regulatory_Capital = EAD × Capital_Rate
        Economic_Capital = Regulatory_Capital × Multiplier
        """
        try:
            # Get capital rate for risk type
            capital_rate = self.regulatory_capital_rates.get(risk_type, 
                                                           self.regulatory_capital_rates['default'])
            
            # Calculate regulatory capital
            result_df = df.withColumn(
                'regulatory_capital',
                col('ead_amount') * lit(capital_rate)
            )
            
            # Calculate economic capital
            result_df = result_df.withColumn(
                'economic_capital',
                col('regulatory_capital') * lit(self.economic_capital_multiplier)
            )
            
            logger.info(f"Calculated capital requirements for {result_df.count()} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating capital: {str(e)}")
            raise


class RARoCCalculator:
    """Risk-Adjusted Return on Capital calculator."""
    
    def __init__(self):
        """Initialize RAROC calculator."""
        self.ead_model = EADModel()
        self.capital_model = CapitalModel()
        
        # Cost components
        self.funding_cost_rate = 0.025    # 2.5% funding cost
        self.operational_cost_rate = 0.005 # 0.5% operational cost
        self.target_roe = 0.15            # 15% target ROE
    
    def calculate_raroc(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """
        Calculate Risk-Adjusted Return on Capital.
        
        RAROC = (Revenue - Expected_Loss - Funding_Cost - Operational_Cost) / Economic_Capital
        
        Where:
        - Revenue = Interest + Fees
        - Expected_Loss = PD × LGD × EAD
        - Funding_Cost = EAD × Funding_Rate
        - Operational_Cost = EAD × Operational_Rate
        """
        try:
            # Calculate EAD if not already present
            if 'ead_amount' not in [c.name for c in df.columns]:
                df = self.ead_model.calculate_ead(df, features)
            
            # Calculate capital requirements
            risk_type = features.get('risk_type', 'corporate')
            df = self.capital_model.calculate_capital(df, risk_type)
            
            # Calculate expected loss
            df = df.withColumn(
                'expected_loss',
                col('pd_score') * col('lgd_score') * col('ead_amount')
            )
            
            # Calculate funding cost
            df = df.withColumn(
                'funding_cost',
                col('ead_amount') * lit(self.funding_cost_rate)
            )
            
            # Calculate operational cost
            df = df.withColumn(
                'operational_cost',
                col('ead_amount') * lit(self.operational_cost_rate)
            )
            
            # Calculate revenue (interest + fees)
            if 'interest_rate' in [c.name for c in df.columns]:
                df = df.withColumn(
                    'interest_revenue',
                    col('ead_amount') * col('interest_rate')
                )
            else:
                # Use a base rate if not provided
                df = df.withColumn(
                    'interest_revenue',
                    col('ead_amount') * lit(0.06)  # 6% base rate
                )
            
            # Add fees if available
            if 'fee_rate' in [c.name for c in df.columns]:
                df = df.withColumn(
                    'fee_revenue',
                    col('ead_amount') * col('fee_rate')
                )
            else:
                df = df.withColumn('fee_revenue', lit(0.0))
            
            df = df.withColumn(
                'total_revenue',
                col('interest_revenue') + col('fee_revenue')
            )
            
            # Calculate net income
            df = df.withColumn(
                'net_income',
                col('total_revenue') - col('expected_loss') - 
                col('funding_cost') - col('operational_cost')
            )
            
            # Calculate RAROC
            df = df.withColumn(
                'raroc',
                when(col('economic_capital') > 0, 
                     col('net_income') / col('economic_capital'))
                .otherwise(lit(0.0))
            )
            
            # Calculate risk-adjusted margin
            df = df.withColumn(
                'risk_adjusted_margin',
                when(col('ead_amount') > 0,
                     col('net_income') / col('ead_amount'))
                .otherwise(lit(0.0))
            )
            
            logger.info(f"Calculated RAROC for {df.count()} records")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating RAROC: {str(e)}")
            raise
    
    def calculate_minimum_price(self, df: DataFrame, features: Dict[str, Any]) -> DataFrame:
        """
        Calculate minimum pricing to achieve target ROE.
        
        Required_Revenue = Expected_Loss + Funding_Cost + Operational_Cost + 
                          (Economic_Capital × Target_ROE)
        """
        try:
            # First calculate RAROC components
            df = self.calculate_raroc(df, features)
            
            # Calculate required revenue for target ROE
            df = df.withColumn(
                'required_revenue',
                col('expected_loss') + col('funding_cost') + col('operational_cost') +
                (col('economic_capital') * lit(self.target_roe))
            )
            
            # Calculate minimum interest rate
            df = df.withColumn(
                'minimum_rate',
                when(col('ead_amount') > 0,
                     col('required_revenue') / col('ead_amount'))
                .otherwise(lit(0.0))
            )
            
            # Calculate pricing components breakdown
            df = df.withColumn(
                'base_rate_component',
                lit(self.funding_cost_rate)
            ).withColumn(
                'risk_premium_component',
                col('expected_loss') / col('ead_amount')
            ).withColumn(
                'operational_component',
                lit(self.operational_cost_rate)
            ).withColumn(
                'capital_component',
                (col('economic_capital') * lit(self.target_roe)) / col('ead_amount')
            )
            
            logger.info(f"Calculated minimum pricing for {df.count()} records")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating minimum price: {str(e)}")
            raise
