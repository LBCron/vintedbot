"""
AI Assistant endpoints
Provides conversational AI assistance for Vinted listing optimization
PLUS Sprint 1 Advanced AI Features (Defects, Pricing, Descriptions)
"""
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from openai import OpenAI

from backend.schemas.ai import ChatRequest, ChatResponse
from backend.core.auth import get_current_user, User
from backend.core.advanced_defect_detector import AdvancedDefectDetector
from backend.core.market_pricing_engine import MarketPricingEngine
from backend.core.description_generator import DescriptionGenerator, DescriptionStyle
from backend.core.session import get_vinted_session

router = APIRouter(prefix="/ai", tags=["ai"])

# Initialize OpenAI client with user's API key
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt for VintedBot Assistant
SYSTEM_PROMPT = """Tu es VintedBot Assistant, un expert en analyse de photos de vêtements et rédaction de descriptions Vinted optimisées.

Ton rôle :
- Aider les utilisateurs à améliorer leurs descriptions de vêtements
- Donner des conseils pour prendre de meilleures photos
- Suggérer des prix appropriés selon la marque, l'état et la catégorie
- Optimiser les titres pour attirer plus d'acheteurs
- Expliquer comment bien catégoriser les articles
- Répondre aux questions sur la vente sur Vinted

Style de réponse :
- Concis et pratique
- Utilise des emojis pour rendre les conseils plus clairs
- Donne des exemples concrets
- Sois encourageant et positif

Tu connais bien :
- Les marques de mode populaires et leur valeur de revente
- Les critères d'état Vinted (Neuf avec étiquette, Très bon état, Bon état, Satisfaisant)
- Les meilleures pratiques pour photographier des vêtements
- Les techniques de description qui convertissent
"""


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Chat with VintedBot AI Assistant
    
    Provides expert advice on:
    - Improving clothing descriptions
    - Photo quality tips
    - Pricing suggestions
    - Title optimization
    - Category selection
    
    Uses GPT-4 for intelligent responses
    """
    try:
        print(f"💬 AI Chat - User message: {request.message[:100]}...")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o for best quality
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract response
        assistant_message = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        print(f"✅ AI Response generated ({tokens_used} tokens)")
        
        return ChatResponse(
            response=assistant_message,
            tokens_used=tokens_used
        )
        
    except Exception as e:
        print(f"❌ AI Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI chat failed: {str(e)}"
        )


# ============================================================================
# SPRINT 1 ADVANCED AI FEATURES
# ============================================================================

@router.post("/analyze-defects")
async def analyze_defects(
    photo_paths: List[str] = Body(...),
    category: Optional[str] = Body(None),
    brand: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """Analyze photos for defects using GPT-4 Vision"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(400, "OpenAI API key not configured")

        detector = AdvancedDefectDetector(api_key)
        assessment = await detector.analyze_multi_photo(photo_paths, category, brand)

        return assessment.to_dict()
    except Exception as e:
        raise HTTPException(500, f"Defect analysis failed: {str(e)}")


@router.post("/suggest-price")
async def suggest_price(
    title: str = Body(...),
    category: str = Body(...),
    brand: Optional[str] = Body(None),
    condition: str = Body("Bon état"),
    size: Optional[str] = Body(None),
    photos_quality_score: float = Body(70.0),
    current_user: User = Depends(get_current_user)
):
    """Get intelligent price recommendation based on market data"""
    try:
        session = get_vinted_session(current_user.id)
        if not session:
            raise HTTPException(400, "Vinted session not configured")

        engine = MarketPricingEngine(session)
        recommendation = await engine.get_price_recommendation(
            title=title,
            category=category,
            brand=brand,
            condition=condition,
            size=size,
            photos_quality_score=photos_quality_score
        )

        return recommendation.to_dict()
    except Exception as e:
        raise HTTPException(500, f"Price suggestion failed: {str(e)}")


@router.post("/generate-description")
async def generate_description(
    item_data: dict = Body(...),
    style: str = Body("casual"),
    include_seo: bool = Body(True),
    include_hashtags: bool = Body(True),
    custom_notes: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """Generate optimized description in chosen style"""
    try:
        generator = DescriptionGenerator()

        # Parse style
        try:
            desc_style = DescriptionStyle(style)
        except ValueError:
            desc_style = DescriptionStyle.CASUAL

        description = generator.generate(
            item_data=item_data,
            style=desc_style,
            include_seo=include_seo,
            include_hashtags=include_hashtags,
            custom_notes=custom_notes
        )

        return {
            "text": description.text,
            "style": description.style.value,
            "char_count": description.char_count,
            "word_count": description.word_count,
            "hashtags": description.hashtags,
            "seo_score": description.seo_score,
            "readability_score": description.readability_score
        }
    except Exception as e:
        raise HTTPException(500, f"Description generation failed: {str(e)}")
