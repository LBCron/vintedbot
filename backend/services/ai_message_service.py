"""
AI-powered message service using GPT-4 Mini for auto-replies
"""
import json
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)


class AIMessageService:
    """Service for AI-powered message analysis and generation"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - AI features will not work")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def analyze_message_intent(
        self,
        message: str,
        article_context: dict
    ) -> dict:
        """
        Analyze buyer message intent using GPT-4 Mini

        Args:
            message: The buyer's message text
            article_context: Dictionary containing article info (title, price, size, etc.)

        Returns:
            Dictionary with intent, confidence, and extracted key info
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return {
                "intention": "unknown",
                "confidence": 0.0,
                "key_info": "AI service not configured",
                "error": "OPENAI_API_KEY not set"
            }

        try:
            prompt = f"""Tu es un assistant IA pour Vinted. Analyse ce message d'un acheteur et détecte son intention.

Message : "{message}"
Article : {article_context.get('title', 'N/A')} - {article_context.get('price', '0')}€ - Taille {article_context.get('size', 'N/A')}

Intentions possibles :
- question_taille : Demande sur la taille
- negociation_prix : Veut négocier le prix
- disponibilite : Demande si disponible
- info_livraison : Questions sur livraison
- etat_article : Questions sur l'état/défauts
- mesures : Demande des mesures précises
- autre : Autre intention

Réponds en JSON avec :
{{
  "intention": "...",
  "confidence": 0.95,
  "key_info": "info importante extraite"
}}"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Message intent analyzed: {result.get('intention')}")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze message intent: {e}")
            return {
                "intention": "autre",
                "confidence": 0.0,
                "key_info": str(e),
                "error": str(e)
            }

    async def generate_response(
        self,
        message: str,
        intention: str,
        article_context: dict,
        user_tone: str = "friendly"  # friendly, professional, casual
    ) -> str:
        """
        Generate automatic response based on message and intent

        Args:
            message: Original buyer message
            intention: Detected intent from analyze_message_intent
            article_context: Article information
            user_tone: Tone of response (friendly, professional, casual)

        Returns:
            Generated response text
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return "Désolé, je ne peux pas générer de réponse automatique pour le moment."

        try:
            # Base templates for common intents
            default_size = "indiquée dans l'annonce"
            templates = {
                "question_taille": f"La taille est {article_context.get('size', default_size)}. C'est une taille {article_context.get('size_type', 'standard')}.",
                "disponibilite": "Oui, l'article est toujours disponible ! 😊",
                "info_livraison": "J'expédie sous 2-3 jours ouvrés via Mondial Relay ou Colissimo selon ta préférence.",
                "etat_article": f"L'article est en {article_context.get('condition', 'bon')} état comme indiqué sur les photos.",
            }

            base_template = templates.get(intention, "")

            tone_descriptions = {
                "friendly": "Chaleureux avec emojis 😊, amical et encourageant",
                "professional": "Poli et formel, professionnel",
                "casual": "Décontracté et simple, direct"
            }

            prompt = f"""Tu es un vendeur {user_tone} sur Vinted. Génère une réponse au message suivant.

Message acheteur : "{message}"
Intention détectée : {intention}
Article : {article_context.get('title', 'N/A')} - {article_context.get('price', '0')}€

Template de base : "{base_template}"

Ton : {user_tone}
{tone_descriptions.get(user_tone, tone_descriptions['friendly'])}

Consignes :
- Réponse naturelle en français
- Max 80 mots
- Répond précisément à la question
- Encourage l'achat subtilement
- Ajoute une question pour engager (si pertinent)
- N'invente PAS d'informations sur l'article
- Utilise les infos de l'article uniquement

Réponse :"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )

            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Generated response for intent {intention}")
            return generated_text

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"Merci pour votre message ! Je vous réponds au plus vite. L'article {article_context.get('title', '')} est toujours disponible."

    async def analyze_and_respond(
        self,
        message: str,
        article_context: dict,
        user_tone: str = "friendly",
        auto_mode: bool = False
    ) -> Dict:
        """
        Complete workflow: analyze intent and generate response

        Args:
            message: Buyer's message
            article_context: Article information
            user_tone: Response tone
            auto_mode: If True, returns response for auto-send, otherwise draft

        Returns:
            Dictionary with analysis and generated response
        """
        # Step 1: Analyze intent
        intent_result = await self.analyze_message_intent(message, article_context)

        # Step 2: Generate response
        if intent_result.get("confidence", 0) > 0.6:
            response_text = await self.generate_response(
                message,
                intent_result["intention"],
                article_context,
                user_tone
            )
        else:
            # Low confidence - generic response
            response_text = f"Bonjour ! Merci pour votre intérêt pour {article_context.get('title', 'cet article')}. Comment puis-je vous aider ?"

        return {
            "intention": intent_result.get("intention"),
            "confidence": intent_result.get("confidence"),
            "key_info": intent_result.get("key_info"),
            "response": response_text,
            "auto_send": auto_mode and intent_result.get("confidence", 0) > 0.8,
            "tone": user_tone
        }

    async def batch_generate_responses(
        self,
        messages: List[Dict],
        user_tone: str = "friendly"
    ) -> List[Dict]:
        """
        Generate responses for multiple messages in batch

        Args:
            messages: List of dicts with 'message' and 'article_context'
            user_tone: Response tone

        Returns:
            List of response dictionaries
        """
        results = []

        for msg_data in messages:
            try:
                result = await self.analyze_and_respond(
                    msg_data["message"],
                    msg_data["article_context"],
                    user_tone
                )
                results.append({
                    "message_id": msg_data.get("id"),
                    **result
                })
            except Exception as e:
                logger.error(f"Failed to process message {msg_data.get('id')}: {e}")
                results.append({
                    "message_id": msg_data.get("id"),
                    "error": str(e),
                    "response": None
                })

        return results
