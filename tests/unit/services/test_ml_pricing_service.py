"""
Unit tests for ML Pricing service
"""
import pytest
import numpy as np
from backend.services.ml_pricing_service import MLPricingService, ml_pricing


class TestMLPricingService:
    """Test suite for ML price prediction service"""
    
    @pytest.mark.asyncio
    async def test_predict_price_with_fallback(self):
        """Test price prediction with fallback (ML not available)"""
        result = await ml_pricing.predict_price(
            category="clothing",
            brand="Zara",
            condition="good"
        )
        
        assert "predicted_price" in result
        assert "confidence" in result
        assert "method" in result
        assert result["method"] == "fallback_heuristic"
        assert result["predicted_price"] > 0
    
    
    @pytest.mark.asyncio
    async def test_predict_price_various_conditions(self):
        """Test price prediction for different conditions"""
        conditions = ["new_with_tags", "new_without_tags", "very_good", "good", "satisfactory"]
        
        prices = []
        for condition in conditions:
            result = await ml_pricing.predict_price(
                category="clothing",
                brand="Zara",
                condition=condition
            )
            prices.append(result["predicted_price"])
        
        # Prices should decrease with condition quality
        assert prices[0] > prices[-1]  # new_with_tags > satisfactory
    
    
    def test_validate_input_valid(self):
        """Test input validation with valid data"""
        data = {
            "category": "clothing",
            "brand": "Zara",
            "condition": "good",
            "views": 10,
            "favorites": 5,
            "age_days": 3
        }
        
        is_valid = ml_pricing._validate_input(data)
        
        assert is_valid is True
    
    
    def test_validate_input_missing_required(self):
        """Test input validation with missing required fields"""
        data = {
            "brand": "Zara",
            # Missing category and condition
        }
        
        is_valid = ml_pricing._validate_input(data)
        
        assert is_valid is False
    
    
    def test_validate_input_negative_numbers(self):
        """Test input validation rejects negative numbers"""
        data = {
            "category": "clothing",
            "condition": "good",
            "views": -10,  # Invalid: negative
            "favorites": 5,
            "age_days": 3
        }
        
        is_valid = ml_pricing._validate_input(data)
        
        assert is_valid is False
    
    
    def test_validate_input_string_too_long(self):
        """Test input validation rejects overly long strings"""
        data = {
            "category": "clothing",
            "brand": "x" * 200,  # Too long (max 100)
            "condition": "good"
        }
        
        is_valid = ml_pricing._validate_input(data)
        
        assert is_valid is False
    
    
    def test_validate_output_valid_price(self):
        """Test output validation with valid price"""
        price = 25.50
        
        validated = ml_pricing._validate_output(price)
        
        assert validated == 25.50
    
    
    def test_validate_output_nan(self):
        """Test output validation handles NaN"""
        price = float('nan')
        
        validated = ml_pricing._validate_output(price)
        
        # Should return fallback price
        assert validated > 0
        assert not np.isnan(validated)
    
    
    def test_validate_output_infinity(self):
        """Test output validation handles infinity"""
        price = float('inf')
        
        validated = ml_pricing._validate_output(price)
        
        # Should return fallback price
        assert validated > 0
        assert not np.isinf(validated)
    
    
    def test_validate_output_clamping_min(self):
        """Test output validation clamps to minimum"""
        price = 0.50  # Below MIN_PRICE (1.0)
        
        validated = ml_pricing._validate_output(price)
        
        assert validated >= MLPricingService.MIN_PRICE
    
    
    def test_validate_output_clamping_max(self):
        """Test output validation clamps to maximum"""
        price = 50000.0  # Above MAX_PRICE (10000.0)
        
        validated = ml_pricing._validate_output(price)
        
        assert validated <= MLPricingService.MAX_PRICE
    
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # High data quality
        data_high = {
            "views": 150,
            "favorites": 15,
            "brand": "Zara",
            "size": "M"
        }
        confidence_high = ml_pricing._calculate_confidence(data_high)
        
        # Low data quality
        data_low = {
            "views": 0,
            "favorites": 0,
            "brand": "unknown",
            "size": "unknown"
        }
        confidence_low = ml_pricing._calculate_confidence(data_low)
        
        # High quality data should have higher confidence
        confidence_levels = ["low", "medium", "high"]
        assert confidence_levels.index(confidence_high) > confidence_levels.index(confidence_low)
    
    
    def test_fallback_prediction_structure(self):
        """Test fallback prediction returns correct structure"""
        result = ml_pricing._fallback_prediction("good")
        
        assert "predicted_price" in result
        assert "confidence" in result
        assert "method" in result
        assert "price_range" in result
        assert "strategies" in result
        
        assert "min" in result["price_range"]
        assert "optimal" in result["price_range"]
        assert "max" in result["price_range"]
        
        assert "fast_sell" in result["strategies"]
        assert "optimal" in result["strategies"]
        assert "premium" in result["strategies"]
    
    
    def test_fallback_prices_configured(self):
        """Test that fallback prices are configured for all conditions"""
        conditions = ["new_with_tags", "new_without_tags", "very_good", "good", "satisfactory"]
        
        for condition in conditions:
            assert condition in MLPricingService.FALLBACK_PRICES
            assert MLPricingService.FALLBACK_PRICES[condition] > 0
