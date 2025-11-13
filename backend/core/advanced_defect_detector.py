"""
Sprint 1 Feature 2A: Advanced Defect Detection with GPT-4 Vision

Ultra-performant AI analysis for clothing defects:
- Defect detection (stains, tears, wear, holes, discoloration)
- Photo quality scoring (sharpness, lighting, framing)
- Precise condition assessment (10-point scale)
- Improvement suggestions for photos
- Automatic condition downgrade recommendations

Uses GPT-4 Vision for visual analysis combined with heuristics.
"""
import base64
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from loguru import logger

import openai
from openai import AsyncOpenAI


class DefectType(Enum):
    """Types of defects that can be detected"""
    STAIN = "stain"
    TEAR = "tear"
    HOLE = "hole"
    WEAR = "wear"
    DISCOLORATION = "discoloration"
    PILLING = "pilling"
    FADING = "fading"
    STRETCHING = "stretching"
    MISSING_BUTTON = "missing_button"
    BROKEN_ZIPPER = "broken_zipper"


class DefectSeverity(Enum):
    """Severity levels for defects"""
    MINOR = "minor"  # Barely visible
    MODERATE = "moderate"  # Visible but acceptable
    MAJOR = "major"  # Significant impact
    CRITICAL = "critical"  # Unwearable


class PhotoQualityAspect(Enum):
    """Aspects of photo quality"""
    SHARPNESS = "sharpness"
    LIGHTING = "lighting"
    FRAMING = "framing"
    BACKGROUND = "background"
    ANGLE = "angle"


@dataclass
class Defect:
    """A detected defect in clothing"""
    type: DefectType
    severity: DefectSeverity
    description: str
    location: str  # e.g., "left sleeve", "front center", "collar"
    confidence: float  # 0.0 to 1.0
    affects_value: bool = True  # Whether it impacts price

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "description": self.description,
            "location": self.location,
            "confidence": self.confidence,
            "affects_value": self.affects_value
        }


@dataclass
class PhotoQualityScore:
    """Quality assessment for a photo"""
    overall_score: float = 0.0  # 0-100
    sharpness_score: float = 0.0
    lighting_score: float = 0.0
    framing_score: float = 0.0
    background_score: float = 0.0
    angle_score: float = 0.0

    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "overall_score": round(self.overall_score, 1),
            "sharpness_score": round(self.sharpness_score, 1),
            "lighting_score": round(self.lighting_score, 1),
            "framing_score": round(self.framing_score, 1),
            "background_score": round(self.background_score, 1),
            "angle_score": round(self.angle_score, 1),
            "issues": self.issues,
            "suggestions": self.suggestions
        }


@dataclass
class ConditionAssessment:
    """Precise condition assessment for clothing"""
    condition_score: float  # 0-10 scale
    condition_label: str  # "Neuf", "Comme neuf", "Très bon état", etc.
    defects: List[Defect]
    overall_quality: str  # "Excellent", "Good", "Fair", "Poor"
    recommended_price_adjustment: float  # Percentage (-30% to +10%)
    detailed_notes: str

    def to_dict(self) -> Dict:
        return {
            "condition_score": round(self.condition_score, 1),
            "condition_label": self.condition_label,
            "defects": [d.to_dict() for d in self.defects],
            "overall_quality": self.overall_quality,
            "recommended_price_adjustment": round(self.recommended_price_adjustment, 1),
            "detailed_notes": self.detailed_notes
        }


class AdvancedDefectDetector:
    """
    Advanced defect detection using GPT-4 Vision

    Features:
    - Multi-photo analysis for comprehensive assessment
    - Precise defect localization
    - Severity classification
    - Photo quality scoring
    - Improvement suggestions
    - Automatic condition assessment
    """

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def analyze_photo(
        self,
        photo_path: str,
        clothing_category: Optional[str] = None
    ) -> Tuple[List[Defect], PhotoQualityScore]:
        """
        Analyze a single photo for defects and quality

        Args:
            photo_path: Path to photo file
            clothing_category: Optional category hint (e.g., "T-shirt", "Jeans")

        Returns:
            (defects_list, quality_score)
        """
        logger.info(f"[DEFECT-DETECT] Analyzing photo: {photo_path}")

        try:
            # Encode image to base64
            image_data = self._encode_image(photo_path)

            # Build prompt
            prompt = self._build_defect_detection_prompt(clothing_category)

            # Call GPT-4 Vision
            response = await self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            # Parse response
            analysis_text = response.choices[0].message.content
            defects, quality_score = self._parse_analysis_response(analysis_text)

            logger.info(
                f"[DEFECT-DETECT] Found {len(defects)} defects, "
                f"quality score: {quality_score.overall_score:.1f}/100"
            )

            return (defects, quality_score)

        except Exception as e:
            logger.error(f"[DEFECT-DETECT] Error analyzing photo: {e}")
            return ([], PhotoQualityScore())

    async def analyze_multi_photo(
        self,
        photo_paths: List[str],
        clothing_category: Optional[str] = None,
        brand: Optional[str] = None
    ) -> ConditionAssessment:
        """
        Analyze multiple photos for comprehensive condition assessment

        Args:
            photo_paths: List of photo file paths
            clothing_category: Optional category hint
            brand: Optional brand name (affects expectations)

        Returns:
            Complete condition assessment
        """
        logger.info(f"[DEFECT-DETECT] Multi-photo analysis: {len(photo_paths)} photos")

        all_defects = []
        quality_scores = []

        # Analyze each photo
        for photo_path in photo_paths:
            defects, quality = await self.analyze_photo(photo_path, clothing_category)
            all_defects.extend(defects)
            quality_scores.append(quality)

        # Deduplicate defects (same type + location)
        unique_defects = self._deduplicate_defects(all_defects)

        # Calculate overall condition score
        condition_score = self._calculate_condition_score(unique_defects)

        # Determine condition label
        condition_label = self._get_condition_label(condition_score)

        # Assess overall quality
        overall_quality = self._assess_overall_quality(condition_score, quality_scores)

        # Calculate price adjustment
        price_adjustment = self._calculate_price_adjustment(unique_defects, condition_score)

        # Generate detailed notes
        detailed_notes = self._generate_detailed_notes(unique_defects, quality_scores)

        assessment = ConditionAssessment(
            condition_score=condition_score,
            condition_label=condition_label,
            defects=unique_defects,
            overall_quality=overall_quality,
            recommended_price_adjustment=price_adjustment,
            detailed_notes=detailed_notes
        )

        logger.info(
            f"[DEFECT-DETECT] Assessment complete: {condition_label} "
            f"({condition_score:.1f}/10), {len(unique_defects)} defects"
        )

        return assessment

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _build_defect_detection_prompt(self, category: Optional[str]) -> str:
        """Build prompt for GPT-4 Vision defect detection"""
        base_prompt = """Analyze this clothing item photo for defects and quality.

Please provide a detailed analysis in the following format:

DEFECTS:
- [Type] at [location]: [description] (Severity: [Minor/Moderate/Major/Critical], Confidence: [0-100]%)

PHOTO QUALITY:
- Sharpness: [0-100]/100
- Lighting: [0-100]/100
- Framing: [0-100]/100
- Background: [0-100]/100
- Angle: [0-100]/100
- Issues: [list any issues]
- Suggestions: [list improvements]

Types of defects to look for:
- Stains (any visible stains or spots)
- Tears (rips or holes in fabric)
- Wear (general wear, fading, stretching)
- Pilling (fabric pills or bobbles)
- Discoloration (uneven color, yellowing)
- Missing buttons or broken zippers
- Any other visible damage

Be thorough and precise in your analysis."""

        if category:
            base_prompt += f"\n\nThis is a {category}. Pay special attention to common issues for this type of clothing."

        return base_prompt

    def _parse_analysis_response(self, text: str) -> Tuple[List[Defect], PhotoQualityScore]:
        """Parse GPT-4 Vision response into structured data"""
        defects = []
        quality = PhotoQualityScore()

        # This is a simplified parser - in production, use more robust parsing
        # or structured output format from GPT-4

        try:
            # Extract defects
            if "DEFECTS:" in text:
                defects_section = text.split("DEFECTS:")[1].split("PHOTO QUALITY:")[0]
                defect_lines = [line.strip() for line in defects_section.split("\n") if line.strip() and line.strip().startswith("-")]

                for line in defect_lines:
                    # Parse defect line (simplified)
                    # Example: "- Stain at left sleeve: Small oil stain (Severity: Minor, Confidence: 85%)"
                    if ":" in line:
                        try:
                            parts = line[2:].split(":")  # Remove "- " prefix
                            if len(parts) >= 2:
                                type_location = parts[0].strip().lower()
                                desc_severity = parts[1].strip()

                                # Extract type
                                defect_type = DefectType.STAIN  # Default
                                for dt in DefectType:
                                    if dt.value in type_location:
                                        defect_type = dt
                                        break

                                # Extract location
                                location = "unknown"
                                if " at " in type_location:
                                    location = type_location.split(" at ")[1].strip()

                                # Extract severity
                                severity = DefectSeverity.MODERATE  # Default
                                if "minor" in desc_severity.lower():
                                    severity = DefectSeverity.MINOR
                                elif "major" in desc_severity.lower():
                                    severity = DefectSeverity.MAJOR
                                elif "critical" in desc_severity.lower():
                                    severity = DefectSeverity.CRITICAL

                                # Extract confidence
                                confidence = 0.7  # Default
                                if "%" in desc_severity:
                                    try:
                                        conf_str = desc_severity.split("%")[0].split(":")[-1].strip()
                                        confidence = float(conf_str) / 100
                                    except:
                                        pass

                                defects.append(Defect(
                                    type=defect_type,
                                    severity=severity,
                                    description=desc_severity.split("(")[0].strip(),
                                    location=location,
                                    confidence=confidence
                                ))
                        except Exception as e:
                            logger.warning(f"Failed to parse defect line: {line}, error: {e}")

            # Extract photo quality scores
            if "PHOTO QUALITY:" in text:
                quality_section = text.split("PHOTO QUALITY:")[1]

                # Extract scores
                for line in quality_section.split("\n"):
                    if "Sharpness:" in line:
                        quality.sharpness_score = self._extract_score(line)
                    elif "Lighting:" in line:
                        quality.lighting_score = self._extract_score(line)
                    elif "Framing:" in line:
                        quality.framing_score = self._extract_score(line)
                    elif "Background:" in line:
                        quality.background_score = self._extract_score(line)
                    elif "Angle:" in line:
                        quality.angle_score = self._extract_score(line)
                    elif "Issues:" in line:
                        issues = line.split("Issues:")[1].strip()
                        if issues and issues != "None":
                            quality.issues = [issues]
                    elif "Suggestions:" in line:
                        suggestions = line.split("Suggestions:")[1].strip()
                        if suggestions and suggestions != "None":
                            quality.suggestions = [suggestions]

                # Calculate overall score
                scores = [
                    quality.sharpness_score,
                    quality.lighting_score,
                    quality.framing_score,
                    quality.background_score,
                    quality.angle_score
                ]
                quality.overall_score = sum(scores) / len(scores) if scores else 0

        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")

        return (defects, quality)

    def _extract_score(self, line: str) -> float:
        """Extract numeric score from line"""
        try:
            # Extract number before /100
            parts = line.split("/100")[0].split(":")
            if len(parts) >= 2:
                return float(parts[-1].strip())
        except:
            pass
        return 70.0  # Default score

    def _deduplicate_defects(self, defects: List[Defect]) -> List[Defect]:
        """Remove duplicate defects (same type + location)"""
        seen = set()
        unique = []

        for defect in defects:
            key = (defect.type.value, defect.location)
            if key not in seen:
                seen.add(key)
                unique.append(defect)

        return unique

    def _calculate_condition_score(self, defects: List[Defect]) -> float:
        """Calculate condition score (0-10) based on defects"""
        base_score = 10.0

        for defect in defects:
            # Deduct points based on severity
            if defect.severity == DefectSeverity.MINOR:
                base_score -= 0.5
            elif defect.severity == DefectSeverity.MODERATE:
                base_score -= 1.5
            elif defect.severity == DefectSeverity.MAJOR:
                base_score -= 3.0
            elif defect.severity == DefectSeverity.CRITICAL:
                base_score -= 5.0

        return max(base_score, 0.0)

    def _get_condition_label(self, score: float) -> str:
        """Convert condition score to label"""
        if score >= 9.5:
            return "Neuf avec étiquette"
        elif score >= 9.0:
            return "Neuf sans étiquette"
        elif score >= 8.5:
            return "Comme neuf"
        elif score >= 7.5:
            return "Très bon état"
        elif score >= 6.0:
            return "Bon état"
        elif score >= 4.0:
            return "État correct"
        else:
            return "Mauvais état"

    def _assess_overall_quality(
        self,
        condition_score: float,
        quality_scores: List[PhotoQualityScore]
    ) -> str:
        """Assess overall quality combining condition and photo quality"""
        if not quality_scores:
            return "Unknown"

        avg_photo_quality = sum(q.overall_score for q in quality_scores) / len(quality_scores)

        # Combined assessment
        combined = (condition_score * 10 + avg_photo_quality) / 2

        if combined >= 85:
            return "Excellent"
        elif combined >= 70:
            return "Good"
        elif combined >= 50:
            return "Fair"
        else:
            return "Poor"

    def _calculate_price_adjustment(self, defects: List[Defect], condition_score: float) -> float:
        """Calculate recommended price adjustment percentage"""
        # Base adjustment on condition score
        if condition_score >= 9.0:
            adjustment = 5.0  # Premium for near-new
        elif condition_score >= 7.5:
            adjustment = 0.0  # No adjustment for good condition
        elif condition_score >= 6.0:
            adjustment = -10.0  # Slight discount
        elif condition_score >= 4.0:
            adjustment = -20.0  # Moderate discount
        else:
            adjustment = -30.0  # Significant discount

        # Additional adjustment for critical defects
        critical_count = sum(1 for d in defects if d.severity == DefectSeverity.CRITICAL)
        adjustment -= critical_count * 10

        return max(adjustment, -50.0)  # Cap at -50%

    def _generate_detailed_notes(
        self,
        defects: List[Defect],
        quality_scores: List[PhotoQualityScore]
    ) -> str:
        """Generate detailed notes about condition"""
        notes = []

        if not defects:
            notes.append("No visible defects detected")
        else:
            notes.append(f"{len(defects)} defect(s) detected:")
            for defect in defects:
                notes.append(
                    f"- {defect.type.value.capitalize()} ({defect.severity.value}) "
                    f"at {defect.location}: {defect.description}"
                )

        # Add photo quality notes
        if quality_scores:
            avg_quality = sum(q.overall_score for q in quality_scores) / len(quality_scores)
            notes.append(f"\nPhoto quality: {avg_quality:.1f}/100")

            # Collect all issues
            all_issues = []
            for q in quality_scores:
                all_issues.extend(q.issues)
            if all_issues:
                notes.append(f"Photo issues: {', '.join(set(all_issues))}")

        return "\n".join(notes)
