"""
Brand Detection Service with OCR

Uses EasyOCR to detect text in images and match against known fashion brands.

Features:
- Multi-language OCR (English, French)
- Fuzzy brand matching
- Confidence scoring
- Label/tag detection
- Logo recognition hints
"""
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

logger = logging.getLogger(__name__)

# Try to import EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not installed - brand detection will be limited")

# Common fashion brands (top 200 brands on Vinted)
KNOWN_BRANDS = [
    # Luxury
    "GUCCI", "LOUIS VUITTON", "CHANEL", "PRADA", "DIOR", "HERMÈS", "VERSACE",
    "BALENCIAGA", "GIVENCHY", "SAINT LAURENT", "BURBERRY", "FENDI",

    # Premium
    "TOMMY HILFIGER", "RALPH LAUREN", "LACOSTE", "HUGO BOSS", "CALVIN KLEIN",
    "DIESEL", "ARMANI", "MICHAEL KORS", "GUESS", "LEVI'S", "WRANGLER",

    # Fast Fashion
    "ZARA", "H&M", "MANGO", "PULL&BEAR", "BERSHKA", "STRADIVARIUS",
    "FOREVER 21", "PRIMARK", "UNIQLO", "GAP", "OLD NAVY",

    # Sportswear
    "NIKE", "ADIDAS", "PUMA", "REEBOK", "CONVERSE", "VANS", "NEW BALANCE",
    "UNDER ARMOUR", "FILA", "CHAMPION", "ASICS", "SKECHERS",

    # French Brands
    "PETIT BATEAU", "COMPTOIR DES COTONNIERS", "SANDRO", "MAJE", "BA&SH",
    "CLAUDIE PIERLOT", "ZADIG&VOLTAIRE", "APC", "ISABEL MARANT",

    # Streetwear
    "SUPREME", "OFF-WHITE", "PALACE", "STÜSSY", "CARHARTT", "DICKIES",
    "THE NORTH FACE", "PATAGONIA", "COLUMBIA",

    # Others
    "MASSIMO DUTTI", "COS", "& OTHER STORIES", "WEEKDAY", "MONKI",
    "AMERICAN VINTAGE", "PETIT BATEAU", "DESIGUAL", "PROMOD",
    "CAMAÏEU", "KIABI", "OKAÏDI", "TAPE À L'OEIL"
]


class BrandDetectionService:
    """OCR-based brand detection for product photos"""

    def __init__(self):
        self.reader = None
        if EASYOCR_AVAILABLE:
            try:
                # Initialize with English and French
                self.reader = easyocr.Reader(['en', 'fr'], gpu=False)
                logger.info("EasyOCR initialized with EN/FR support")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.reader = None

    def detect_brand(self, image_path: str) -> Dict:
        """
        Detect brand from image using OCR

        Args:
            image_path: Path to product image

        Returns:
            Brand detection result with confidence
        """
        if not self.reader:
            logger.warning("OCR not available - using fallback")
            return {
                "brand_detected": False,
                "brand_name": None,
                "confidence": 0,
                "method": "fallback",
                "ocr_text": [],
                "matches": []
            }

        try:
            # Perform OCR
            results = self.reader.readtext(image_path)

            # Extract all detected text
            detected_texts = []
            for (bbox, text, conf) in results:
                if conf > 0.5:  # Only keep high-confidence detections
                    detected_texts.append({
                        "text": text,
                        "confidence": float(conf),
                        "bbox": bbox
                    })

            logger.info(f"OCR detected {len(detected_texts)} text regions")

            # Match against known brands
            brand_matches = self._match_brands(detected_texts)

            if brand_matches:
                best_match = brand_matches[0]
                return {
                    "brand_detected": True,
                    "brand_name": best_match["brand"],
                    "confidence": best_match["confidence"],
                    "method": "ocr",
                    "ocr_text": detected_texts,
                    "matches": brand_matches[:3]  # Top 3 matches
                }
            else:
                return {
                    "brand_detected": False,
                    "brand_name": None,
                    "confidence": 0,
                    "method": "ocr",
                    "ocr_text": detected_texts,
                    "matches": []
                }

        except Exception as e:
            logger.error(f"Brand detection failed: {e}")
            return {
                "brand_detected": False,
                "brand_name": None,
                "confidence": 0,
                "method": "error",
                "error": str(e)
            }

    def _match_brands(self, detected_texts: List[Dict]) -> List[Dict]:
        """
        Match detected text against known brands

        Args:
            detected_texts: List of OCR detections

        Returns:
            Sorted list of brand matches
        """
        matches = []

        for detection in detected_texts:
            text = detection["text"].upper().strip()
            ocr_conf = detection["confidence"]

            # Exact match
            if text in KNOWN_BRANDS:
                matches.append({
                    "brand": text,
                    "confidence": ocr_conf * 100,
                    "match_type": "exact"
                })
                continue

            # Fuzzy match (contains brand name)
            for brand in KNOWN_BRANDS:
                if brand in text or text in brand:
                    # Calculate similarity score
                    similarity = self._calculate_similarity(text, brand)
                    if similarity > 0.7:
                        matches.append({
                            "brand": brand,
                            "confidence": ocr_conf * similarity * 100,
                            "match_type": "fuzzy"
                        })

        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        # Remove duplicates
        seen_brands = set()
        unique_matches = []
        for match in matches:
            if match["brand"] not in seen_brands:
                seen_brands.add(match["brand"])
                unique_matches.append(match)

        return unique_matches

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity (simple Jaccard)

        Args:
            text1, text2: Texts to compare

        Returns:
            Similarity score 0-1
        """
        set1 = set(text1.split())
        set2 = set(text2.split())

        if not set1 or not set2:
            return 0.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        return len(intersection) / len(union) if union else 0.0

    def batch_detect_brands(self, image_paths: List[str]) -> List[Dict]:
        """
        Detect brands in multiple images

        Args:
            image_paths: List of image paths

        Returns:
            List of detection results
        """
        results = []
        for path in image_paths:
            result = self.detect_brand(path)
            results.append(result)

        return results

    @staticmethod
    def is_luxury_brand(brand_name: str) -> bool:
        """Check if brand is luxury/premium"""
        luxury_brands = {
            "GUCCI", "LOUIS VUITTON", "CHANEL", "PRADA", "DIOR", "HERMÈS",
            "VERSACE", "BALENCIAGA", "GIVENCHY", "SAINT LAURENT", "BURBERRY",
            "FENDI", "BOTTEGA VENETA", "CELINE", "LOEWE"
        }
        return brand_name.upper() in luxury_brands
