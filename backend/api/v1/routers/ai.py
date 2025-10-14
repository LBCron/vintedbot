"""
AI Assistant endpoints
Provides conversational AI assistance for Vinted listing optimization
"""
import os
from fastapi import APIRouter, HTTPException
from openai import OpenAI

from backend.schemas.ai import ChatRequest, ChatResponse

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
