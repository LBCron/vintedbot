"""
AI-powered image enhancement service using GPT-4 Vision
"""
import logging
import base64
import os
from typing import Dict, List
from PIL import Image, ImageEnhance, ImageFilter
import io

logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - image analysis will be limited")


class ImageEnhancerService:
    """Service for AI-powered image enhancement"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key) if (api_key and OPENAI_AVAILABLE) else None

    async def analyze_image_quality(self, image_path: str) -> Dict:
        """
        Analyze image quality using GPT-4 Vision

        Args:
            image_path: Path to image file

        Returns:
            Quality analysis with scores and recommendations
        """
        if not self.client:
            logger.warning("OpenAI client not available - using fallback analysis")
            return self._fallback_analysis()

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            # Analyze with GPT-4 Vision
            response = await self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this product photo and evaluate its quality.

Rate (0-10) for:
- Brightness
- Sharpness
- Contrast
- Framing
- Background quality

Provide recommendations for improvement.

Respond in JSON:
{
  "brightness_score": 7,
  "sharpness_score": 8,
  "contrast_score": 6,
  "framing_score": 9,
  "background_score": 7,
  "overall_score": 7.4,
  "recommendations": ["Increase brightness", "Improve contrast"],
  "auto_enhance_suggested": true
}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }],
                response_format={"type": "json_object"},
                max_tokens=500
            )

            result = eval(response.choices[0].message.content)
            logger.info(f"Image analyzed: overall score {result.get('overall_score')}")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze image with AI: {e}")
            return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict:
        """Fallback analysis when AI is unavailable"""
        return {
            "brightness_score": 7.0,
            "sharpness_score": 7.0,
            "contrast_score": 7.0,
            "framing_score": 8.0,
            "background_score": 7.0,
            "overall_score": 7.2,
            "recommendations": ["AI analysis unavailable - using basic enhancement"],
            "auto_enhance_suggested": True
        }

    def auto_enhance_image(
        self,
        image_path: str,
        enhancements: Dict
    ) -> str:
        """
        Apply automatic enhancements to image

        Args:
            image_path: Path to source image
            enhancements: Dict of enhancement values (brightness, contrast, etc.)

        Returns:
            Path to enhanced image
        """
        try:
            img = Image.open(image_path)

            # Brightness adjustment
            if enhancements.get('brightness', 0) != 0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1 + enhancements['brightness'] / 100)

            # Contrast adjustment
            if enhancements.get('contrast', 0) != 0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1 + enhancements['contrast'] / 100)

            # Sharpness adjustment
            if enhancements.get('sharpness', 0) != 0:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1 + enhancements['sharpness'] / 100)

            # Color/Saturation
            if enhancements.get('saturation', 0) != 0:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1 + enhancements['saturation'] / 100)

            # Unsharp mask for detail
            if enhancements.get('sharpen', False):
                img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

            # Save enhanced image
            output_path = image_path.replace('.jpg', '_enhanced.jpg')
            img.save(output_path, 'JPEG', quality=95)

            logger.info(f"Image enhanced and saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to enhance image: {e}")
            return image_path  # Return original if enhancement fails

    async def batch_enhance(
        self,
        image_paths: List[str],
        auto_apply: bool = False
    ) -> List[Dict]:
        """
        Analyze and enhance batch of images

        Args:
            image_paths: List of image file paths
            auto_apply: Whether to apply enhancements automatically

        Returns:
            List of results with analysis and enhanced paths
        """
        results = []

        for path in image_paths:
            try:
                # Analyze
                analysis = await self.analyze_image_quality(path)

                # Auto-enhance if suggested and enabled
                enhanced_path = None
                if auto_apply and analysis.get('auto_enhance_suggested'):
                    # Calculate enhancements based on scores
                    enhancements = {
                        'brightness': (10 - analysis.get('brightness_score', 7)) * 5,
                        'contrast': (10 - analysis.get('contrast_score', 7)) * 5,
                        'sharpness': (10 - analysis.get('sharpness_score', 7)) * 3,
                        'sharpen': analysis.get('sharpness_score', 7) < 7
                    }
                    enhanced_path = self.auto_enhance_image(path, enhancements)

                results.append({
                    'original_path': path,
                    'enhanced_path': enhanced_path,
                    'analysis': analysis,
                    'success': True
                })

            except Exception as e:
                logger.error(f"Failed to process image {path}: {e}")
                results.append({
                    'original_path': path,
                    'enhanced_path': None,
                    'analysis': None,
                    'success': False,
                    'error': str(e)
                })

        logger.info(f"Batch enhanced {len(results)} images")
        return results

    def smart_enhance(self, image_path: str) -> str:
        """
        Apply smart automatic enhancement using image analysis

        Args:
            image_path: Path to image

        Returns:
            Path to enhanced image
        """
        try:
            img = Image.open(image_path)

            # Auto-enhance with standard settings
            enhancements = {
                'brightness': 10,  # +10%
                'contrast': 15,    # +15%
                'sharpness': 10,   # +10%
                'sharpen': True
            }

            return self.auto_enhance_image(image_path, enhancements)

        except Exception as e:
            logger.error(f"Smart enhancement failed: {e}")
            return image_path
