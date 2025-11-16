"""
ML Pricing Service
Advanced machine learning price prediction using RandomForest
"""
import os
import json
import pickle
from typing import Dict, Optional, List
from loguru import logger
from datetime import datetime
import numpy as np

# ML imports (installed via requirements.txt)
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import LabelEncoder
    ML_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ scikit-learn not available - ML pricing disabled")
    ML_AVAILABLE = False


class MLPricingService:
    """
    Advanced ML-powered pricing service

    Features:
    - RandomForest price prediction
    - Feature engineering
    - Model training from historical data
    - Confidence scores
    - Market trend analysis
    """

    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.model_path = "/app/backend/ml_models/pricing_model.pkl"
        self.encoders_path = "/app/backend/ml_models/label_encoders.pkl"
        self.is_trained = False

        # Load existing model if available
        self._load_model()

    def _load_model(self):
        """Load trained model from disk"""
        if not ML_AVAILABLE:
            return

        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("✅ Loaded pricing model")
                self.is_trained = True

            if os.path.exists(self.encoders_path):
                with open(self.encoders_path, 'rb') as f:
                    self.label_encoders = pickle.load(f)
                logger.info("✅ Loaded label encoders")

        except Exception as e:
            logger.warning(f"⚠️ Could not load model: {e}")

    def _save_model(self):
        """Save trained model to disk"""
        if not ML_AVAILABLE or not self.model:
            return

        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)

            with open(self.encoders_path, 'wb') as f:
                pickle.dump(self.label_encoders, f)

            logger.info("✅ Saved pricing model")

        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")

    def _prepare_features(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        condition: Optional[str] = None,
        color: Optional[str] = None,
        views: int = 0,
        favorites: int = 0,
        age_days: int = 0
    ) -> np.ndarray:
        """
        Prepare feature vector for prediction

        Args:
            category: Item category
            brand: Brand name
            size: Size
            condition: Condition
            color: Color
            views: Number of views
            favorites: Number of favorites
            age_days: Days since listing

        Returns:
            Feature vector
        """
        features = []

        # Categorical features (encoded)
        categorical_features = {
            'category': category or 'unknown',
            'brand': brand or 'unknown',
            'size': size or 'unknown',
            'condition': condition or 'unknown',
            'color': color or 'unknown'
        }

        for feature_name, value in categorical_features.items():
            if feature_name not in self.label_encoders:
                # Create new encoder
                self.label_encoders[feature_name] = LabelEncoder()
                self.label_encoders[feature_name].fit([value, 'unknown'])

            encoder = self.label_encoders[feature_name]

            # Handle unseen labels
            if value not in encoder.classes_:
                encoder.classes_ = np.append(encoder.classes_, value)

            encoded = encoder.transform([value])[0]
            features.append(encoded)

        # Numerical features
        features.extend([
            views,
            favorites,
            age_days,
            views / max(age_days, 1),  # Views per day
            favorites / max(views, 1)  # Favorite rate
        ])

        return np.array(features).reshape(1, -1)

    async def train_model(
        self,
        training_data: List[Dict]
    ) -> bool:
        """
        Train pricing model on historical data

        Args:
            training_data: List of items with actual prices
                Each item should have: category, brand, size, condition, price, etc.

        Returns:
            True if training successful
        """
        if not ML_AVAILABLE:
            logger.warning("ML not available - cannot train model")
            return False

        if len(training_data) < 10:
            logger.warning("Not enough data to train model (need at least 10 items)")
            return False

        logger.info(f"🎓 Training pricing model on {len(training_data)} items")

        try:
            # Prepare features and labels
            X = []
            y = []

            for item in training_data:
                if 'price' not in item or item['price'] is None:
                    continue

                features = self._prepare_features(
                    category=item.get('category'),
                    brand=item.get('brand'),
                    size=item.get('size'),
                    condition=item.get('condition'),
                    color=item.get('color'),
                    views=item.get('views', 0),
                    favorites=item.get('favorites', 0),
                    age_days=item.get('age_days', 0)
                )

                X.append(features[0])
                y.append(item['price'])

            X = np.array(X)
            y = np.array(y)

            # Train RandomForest model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )

            self.model.fit(X, y)

            # Calculate training score
            score = self.model.score(X, y)
            logger.info(f"✅ Model trained - R² score: {score:.3f}")

            self.is_trained = True
            self._save_model()

            return True

        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            return False

    async def predict_price(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        condition: Optional[str] = None,
        color: Optional[str] = None,
        views: int = 0,
        favorites: int = 0,
        age_days: int = 0,
        market_data: Optional[Dict] = None
    ) -> Dict:
        """
        Predict optimal price using ML model

        Args:
            category: Item category
            brand: Brand name
            size: Size
            condition: Condition
            color: Color
            views: Number of views
            favorites: Number of favorites
            age_days: Days since listing
            market_data: Optional market statistics from scraper

        Returns:
            Price prediction with confidence
        """
        if not ML_AVAILABLE:
            return {
                "predicted_price": None,
                "confidence": 0,
                "method": "unavailable",
                "message": "ML not available"
            }

        if not self.is_trained or self.model is None:
            # Fallback to rule-based pricing
            return await self._rule_based_pricing(
                category=category,
                brand=brand,
                condition=condition,
                market_data=market_data
            )

        try:
            # Prepare features
            features = self._prepare_features(
                category=category,
                brand=brand,
                size=size,
                condition=condition,
                color=color,
                views=views,
                favorites=favorites,
                age_days=age_days
            )

            # Predict
            prediction = self.model.predict(features)[0]

            # Get prediction confidence (using decision tree predictions)
            predictions = [tree.predict(features)[0] for tree in self.model.estimators_]
            std_dev = np.std(predictions)

            # Lower std = higher confidence
            confidence = max(0, 100 - (std_dev / prediction * 100)) if prediction > 0 else 0

            # Adjust with market data if available
            if market_data and market_data.get('median_price'):
                market_price = market_data['median_price']

                # Blend ML prediction with market data (70% ML, 30% market)
                blended_price = (prediction * 0.7) + (market_price * 0.3)

                return {
                    "predicted_price": round(blended_price, 2),
                    "ml_price": round(prediction, 2),
                    "market_price": round(market_price, 2),
                    "confidence": round(confidence, 1),
                    "method": "ml_market_blend",
                    "message": "ML prediction blended with market data"
                }

            return {
                "predicted_price": round(prediction, 2),
                "confidence": round(confidence, 1),
                "method": "ml",
                "message": "ML-based prediction"
            }

        except Exception as e:
            logger.error(f"❌ Price prediction error: {e}")
            return await self._rule_based_pricing(
                category=category,
                brand=brand,
                condition=condition,
                market_data=market_data
            )

    async def _rule_based_pricing(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        condition: Optional[str] = None,
        market_data: Optional[Dict] = None
    ) -> Dict:
        """
        Fallback rule-based pricing

        Args:
            category: Item category
            brand: Brand name
            condition: Condition
            market_data: Market statistics

        Returns:
            Price recommendation
        """
        # Use market data if available
        if market_data and market_data.get('median_price'):
            base_price = market_data['median_price']
        else:
            # Default base prices by category
            category_prices = {
                'vetements': 15,
                'chaussures': 25,
                'accessoires': 10,
                'maroquinerie': 30
            }
            base_price = category_prices.get(category, 20)

        # Brand multiplier
        premium_brands = ['nike', 'adidas', 'zara', 'h&m', 'mango']
        luxury_brands = ['gucci', 'louis vuitton', 'chanel', 'dior', 'prada']

        multiplier = 1.0
        if brand:
            brand_lower = brand.lower()
            if any(b in brand_lower for b in luxury_brands):
                multiplier = 2.5
            elif any(b in brand_lower for b in premium_brands):
                multiplier = 1.3

        # Condition multiplier
        condition_multipliers = {
            "neuf_avec_etiquette": 1.2,
            "neuf_sans_etiquette": 1.1,
            "tres_bon_etat": 1.0,
            "bon_etat": 0.85,
            "satisfaisant": 0.7
        }

        condition_mult = condition_multipliers.get(condition, 1.0)

        # Calculate price
        price = base_price * multiplier * condition_mult

        return {
            "predicted_price": round(price, 2),
            "confidence": 50,
            "method": "rule_based",
            "message": "Rule-based pricing (ML model not trained)"
        }

    async def get_optimal_price_strategy(
        self,
        item_data: Dict,
        market_data: Optional[Dict] = None
    ) -> Dict:
        """
        Get complete pricing strategy recommendation

        Args:
            item_data: Item details
            market_data: Optional market statistics

        Returns:
            Complete pricing strategy
        """
        # Get ML prediction
        prediction = await self.predict_price(
            category=item_data.get('category'),
            brand=item_data.get('brand'),
            size=item_data.get('size'),
            condition=item_data.get('condition'),
            color=item_data.get('color'),
            views=item_data.get('views', 0),
            favorites=item_data.get('favorites', 0),
            age_days=item_data.get('age_days', 0),
            market_data=market_data
        )

        recommended_price = prediction['predicted_price']

        if recommended_price is None:
            recommended_price = 20  # Default

        # Price strategy
        strategy = {
            "recommended_price": recommended_price,
            "fast_sell_price": round(recommended_price * 0.85, 2),  # 15% discount
            "optimal_price": recommended_price,
            "premium_price": round(recommended_price * 1.15, 2),  # 15% premium
            "confidence": prediction['confidence'],
            "method": prediction['method'],
            "recommendation": self._get_strategy_recommendation(prediction['confidence'])
        }

        return strategy

    def _get_strategy_recommendation(self, confidence: float) -> str:
        """Get strategy recommendation based on confidence"""
        if confidence >= 80:
            return "High confidence - Use optimal price"
        elif confidence >= 60:
            return "Medium confidence - Consider market trends"
        else:
            return "Low confidence - Start with premium price and adjust"


# Global instance
ml_pricing_service = MLPricingService()
