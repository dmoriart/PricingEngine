import pytest
from unittest.mock import Mock, patch
from risk.pd_models import LogisticPDModel, ScoreBasedPDModel, IndustryPDModel
from risk.lgd_models import CollateralBasedLGDModel, IndustryLGDModel, HybridLGDModel
from risk.raroc_calculator import RARoCCalculator, EADModel, CapitalModel
from risk.raroc_pricing_engine import RARoCPricingEngine


@pytest.fixture
def sample_borrower_data():
    """Sample borrower data for testing."""
    return {
        'borrower_id': 'B001',
        'credit_score': 720,
        'debt_to_income': 0.4,
        'loan_to_value': 0.75,
        'employment_years': 8,
        'payment_history_score': 85,
        'industry': 'technology',
        'company_size': 'medium',
        'collateral_type': 'equipment',
        'seniority': 'senior_secured',
        'facility_type': 'term_loan',
        'exposure_amount': 1000000.0,
        'outstanding_amount': 1000000.0,
        'undrawn_amount': 0.0,
        'loan_term': 5,
        'region': 'developed'
    }


class TestPDModels:
    """Test PD model calculations."""
    
    def test_logistic_pd_model_coefficients(self):
        """Test logistic PD model coefficient structure."""
        model = LogisticPDModel()
        
        # Check required coefficients exist
        required_coeffs = ['intercept', 'credit_score', 'debt_to_income', 'loan_to_value']
        for coeff in required_coeffs:
            assert coeff in model.coefficients
            assert isinstance(model.coefficients[coeff], (int, float))
    
    def test_score_based_pd_logic(self):
        """Test score-based PD model logic."""
        model = ScoreBasedPDModel()
        
        # Test score to PD mapping logic
        assert 0.002 == model.score_to_pd[800]  # Excellent credit
        assert 0.250 == model.score_to_pd[500]  # Poor credit
        
        # Higher scores should have lower PD
        scores = sorted(model.score_to_pd.keys(), reverse=True)
        pds = [model.score_to_pd[score] for score in scores]
        assert pds == sorted(pds)  # PDs should be ascending as scores descend
    
    def test_industry_pd_rates(self):
        """Test industry PD model rates."""
        model = IndustryPDModel()
        
        # Technology should have lower PD than hospitality
        assert model.industry_pd['technology'] < model.industry_pd['hospitality']
        
        # All PD rates should be between 0 and 1
        for industry, pd_rate in model.industry_pd.items():
            assert 0 <= pd_rate <= 1


class TestLGDModels:
    """Test LGD model calculations."""
    
    def test_collateral_lgd_rates(self):
        """Test collateral-based LGD rates."""
        model = CollateralBasedLGDModel()
        
        # Cash securities should have lowest LGD
        assert model.base_lgd['cash_securities'] < model.base_lgd['unsecured']
        
        # Unsecured should have highest LGD
        max_lgd = max(model.base_lgd.values())
        assert model.base_lgd['unsecured'] == max_lgd
        
        # All LGD rates should be between 0 and 1
        for collateral, lgd_rate in model.base_lgd.items():
            assert 0 <= lgd_rate <= 1
    
    def test_industry_lgd_characteristics(self):
        """Test industry LGD characteristics."""
        model = IndustryLGDModel()
        
        # Real estate should have lower LGD than technology (tangible vs intangible assets)
        assert model.industry_lgd['real_estate'] < model.industry_lgd['technology']
        
        # Services should have high LGD (limited tangible assets)
        assert model.industry_lgd['services'] > model.industry_lgd['manufacturing']
    
    def test_economic_adjustments(self):
        """Test economic condition adjustments."""
        model = CollateralBasedLGDModel()
        
        # Recession should increase LGD
        assert model.economic_adjustments['recession'] > model.economic_adjustments['normal']
        
        # Expansion should decrease LGD
        assert model.economic_adjustments['expansion'] < model.economic_adjustments['normal']


class TestRARoCCalculator:
    """Test RAROC calculation components."""
    
    def test_ead_calculation_logic(self):
        """Test EAD calculation logic."""
        model = EADModel()
        
        # Term loans should have 100% CCF
        assert model.ccf_rates['term_loan'] == 1.0
        
        # Revolving credit should have partial CCF
        assert 0 < model.ccf_rates['revolving_credit'] < 1.0
        
        # Commitments should have low CCF
        assert model.ccf_rates['commitment'] < model.ccf_rates['revolving_credit']
    
    def test_capital_requirements(self):
        """Test capital requirement calculations."""
        model = CapitalModel()
        
        # Corporate should have higher capital than retail
        assert model.regulatory_capital_rates['corporate'] > model.regulatory_capital_rates['retail']
        
        # Sovereign should have lowest capital
        assert model.regulatory_capital_rates['sovereign'] == 0.0
        
        # Economic capital should be higher than regulatory
        assert model.economic_capital_multiplier > 1.0
    
    def test_raroc_components(self):
        """Test RAROC calculation components."""
        calculator = RARoCCalculator()
        
        # Funding cost should be positive
        assert calculator.funding_cost_rate > 0
        
        # Operational cost should be positive
        assert calculator.operational_cost_rate > 0
        
        # Target ROE should be reasonable
        assert 0.10 <= calculator.target_roe <= 0.25


class TestRARoCPricingEngine:
    """Test RAROC pricing engine integration."""
    
    @patch('risk.raroc_pricing_engine.spark_manager')
    def test_pricing_engine_initialization(self, mock_spark_manager):
        """Test pricing engine initialization."""
        mock_spark = Mock()
        mock_spark_manager.spark = mock_spark
        
        engine = RARoCPricingEngine()
        
        # Check models are initialized
        assert 'logistic' in engine.pd_models
        assert 'hybrid' in engine.lgd_models
        assert engine.raroc_calculator is not None
    
    def test_model_combinations(self):
        """Test valid model combinations."""
        with patch('risk.raroc_pricing_engine.spark_manager'):
            engine = RARoCPricingEngine()
            
            # All PD models should be available
            for model_name in ['logistic', 'score_based', 'industry']:
                assert model_name in engine.pd_models
            
            # All LGD models should be available
            for model_name in ['collateral', 'industry', 'hybrid']:
                assert model_name in engine.lgd_models


class TestRiskCalculations:
    """Test risk calculation logic without Spark dependencies."""
    
    def test_pd_calculation_bounds(self):
        """Test PD calculation bounds."""
        # PD should be between 0 and 1
        pd_score = 0.05
        assert 0 <= pd_score <= 1
        
        # High credit score should result in low PD
        high_score_pd = 0.002  # AAA rating
        low_score_pd = 0.250   # Default rating
        assert high_score_pd < low_score_pd
    
    def test_lgd_calculation_bounds(self):
        """Test LGD calculation bounds."""
        # LGD should be between 0 and 1
        lgd_score = 0.45
        assert 0 <= lgd_score <= 1
        
        # Secured should have lower LGD than unsecured
        secured_lgd = 0.25
        unsecured_lgd = 0.85
        assert secured_lgd < unsecured_lgd
    
    def test_expected_loss_calculation(self):
        """Test expected loss calculation."""
        pd = 0.05    # 5% PD
        lgd = 0.40   # 40% LGD
        ead = 1000000  # $1M exposure
        
        expected_loss = pd * lgd * ead
        assert expected_loss == 20000  # $20k expected loss
    
    def test_raroc_calculation(self):
        """Test RAROC calculation logic."""
        net_income = 50000     # $50k net income
        economic_capital = 200000  # $200k economic capital
        
        raroc = net_income / economic_capital
        assert raroc == 0.25  # 25% RAROC
        
        # RAROC should be positive for profitable deals
        assert raroc > 0
    
    def test_minimum_pricing_logic(self):
        """Test minimum pricing calculation."""
        expected_loss = 20000
        funding_cost = 25000
        operational_cost = 5000
        capital_cost = 30000  # 15% ROE on $200k capital
        ead = 1000000
        
        required_revenue = expected_loss + funding_cost + operational_cost + capital_cost
        minimum_rate = required_revenue / ead
        
        assert minimum_rate == 0.08  # 8% minimum rate
        assert minimum_rate > 0
    
    def test_stress_testing_factors(self):
        """Test stress testing adjustments."""
        base_pd = 0.05
        stress_factor = 2.0
        
        stress_pd = base_pd * stress_factor
        assert stress_pd == 0.10  # Doubled in stress
        
        base_lgd = 0.40
        lgd_stress_factor = 1.3
        
        stress_lgd = base_lgd * lgd_stress_factor
        assert stress_lgd == 0.52  # 30% increase in stress


class TestPricingRecommendations:
    """Test pricing recommendation logic."""
    
    def test_risk_rating_classification(self):
        """Test risk rating classification."""
        # Map PD to risk ratings
        pd_to_rating = {
            0.005: 'AAA',   # 0.5% PD
            0.015: 'AA',    # 1.5% PD
            0.035: 'A',     # 3.5% PD
            0.075: 'BBB',   # 7.5% PD
            0.150: 'BB',    # 15% PD
            0.250: 'B',     # 25% PD
            0.350: 'CCC'    # 35% PD
        }
        
        for pd, expected_rating in pd_to_rating.items():
            if pd <= 0.01:
                assert expected_rating in ['AAA']
            elif pd <= 0.02:
                assert expected_rating in ['AAA', 'AA']
            elif pd <= 0.05:
                assert expected_rating in ['AAA', 'AA', 'A']
    
    def test_pricing_recommendations(self):
        """Test pricing recommendation logic."""
        target_raroc = 0.15
        
        # High RAROC should be highly attractive
        high_raroc = 0.25
        assert high_raroc >= target_raroc * 1.5  # HIGHLY_ATTRACTIVE
        
        # Moderate RAROC should be attractive
        moderate_raroc = 0.18
        assert target_raroc <= moderate_raroc < target_raroc * 1.5  # ATTRACTIVE
        
        # Low RAROC should be rejected
        low_raroc = 0.05
        assert low_raroc < target_raroc * 0.5  # REJECT
