"""
Sprint 2 Feature: AI-Powered Auto-Messages
Automatically responds to Vinted messages with intelligent, context-aware replies
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
import re
from loguru import logger
import openai
import os

from backend.core.vinted_api_client import VintedAPIClient
from backend.core.session import get_vinted_session


class MessageType(Enum):
    """Types of messages we can detect"""
    PRICE_QUESTION = "price_question"       # "Can you lower the price?"
    AVAILABILITY = "availability"           # "Is this still available?"
    SHIPPING_QUESTION = "shipping"          # "How much is shipping?"
    SIZE_QUESTION = "size"                  # "What size is this?"
    CONDITION_QUESTION = "condition"        # "What condition?"
    GENERAL_QUESTION = "general"            # Other questions
    NEGOTIATION = "negotiation"             # "Would you accept X€?"
    THANK_YOU = "thank_you"                 # "Thanks!"
    GREETING = "greeting"                   # "Hi!"


class ResponseTone(Enum):
    """Tone of auto-responses"""
    FRIENDLY = "friendly"          # Warm and casual
    PROFESSIONAL = "professional"  # Polite and formal
    CONCISE = "concise"           # Short and to the point
    ENTHUSIASTIC = "enthusiastic"  # Excited and helpful


@dataclass
class MessageTemplate:
    """Template for common responses"""
    message_type: MessageType
    template: str
    variables: List[str]  # Variables that can be filled in

    def format(self, **kwargs) -> str:
        """Format template with variables"""
        return self.template.format(**kwargs)


@dataclass
class ConversationContext:
    """Context about a conversation"""
    conversation_id: str
    other_user_id: str
    other_username: str
    item_id: Optional[str] = None
    item_title: Optional[str] = None
    item_price: Optional[float] = None
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    auto_replied: bool = False


class MessageClassifier:
    """Classifies incoming messages to determine intent"""

    # Keywords for classification
    KEYWORDS = {
        MessageType.PRICE_QUESTION: [
            'prix', 'price', 'combien', 'coute', 'coût', 'tarif',
            'négocier', 'négociation', 'discount', 'réduction', 'baisser'
        ],
        MessageType.AVAILABILITY: [
            'disponible', 'available', 'encore', 'still', 'dispo', 'vendu'
        ],
        MessageType.SHIPPING_QUESTION: [
            'livraison', 'shipping', 'frais', 'envoi', 'expédition',
            'transporter', 'recevoir', 'délai'
        ],
        MessageType.SIZE_QUESTION: [
            'taille', 'size', 'dimension', 'mesure', 'fit'
        ],
        MessageType.CONDITION_QUESTION: [
            'état', 'condition', 'défaut', 'damage', 'usure', 'wear', 'qualité'
        ],
        MessageType.NEGOTIATION: [
            'accepter', 'accept', 'offre', 'offer', 'propose',
            '€', 'euros', 'eur'
        ],
        MessageType.THANK_YOU: [
            'merci', 'thank', 'thanks', 'super', 'parfait', 'great'
        ],
        MessageType.GREETING: [
            'bonjour', 'salut', 'hello', 'hi', 'hey', 'coucou'
        ]
    }

    @classmethod
    def classify(cls, message_text: str) -> MessageType:
        """Classify message based on keywords"""
        message_lower = message_text.lower()

        # Score each type
        scores = {}
        for msg_type, keywords in cls.KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                scores[msg_type] = score

        if scores:
            # Return type with highest score
            return max(scores.items(), key=lambda x: x[1])[0]

        return MessageType.GENERAL_QUESTION

    @classmethod
    def extract_price_offer(cls, message_text: str) -> Optional[float]:
        """Extract price from negotiation message"""
        # Match patterns like "20€", "20 euros", "20.5€"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*€',
            r'(\d+(?:\.\d+)?)\s*euros?',
            r'(\d+(?:\.\d+)?)\s*eur'
        ]

        for pattern in patterns:
            match = re.search(pattern, message_text.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass

        return None


class TemplateLibrary:
    """Library of pre-defined response templates"""

    TEMPLATES = {
        MessageType.AVAILABILITY: [
            "Oui, l'article est toujours disponible ! 😊 N'hésite pas si tu as des questions.",
            "Hello ! Oui c'est encore dispo, tu peux l'acheter directement.",
            "Oui disponible ! Je peux l'envoyer dès demain si tu commandes aujourd'hui. [PACKAGE]"
        ],

        MessageType.PRICE_QUESTION: [
            "Le prix affiché est déjà le meilleur que je peux faire pour cet article. 😊",
            "Désolé(e), le prix est ferme pour le moment. Mais je fais des envois rapides ! [PACKAGE]",
            "C'est déjà un bon prix pour la qualité, mais si tu prends plusieurs articles je peux voir ! 😉"
        ],

        MessageType.SHIPPING_QUESTION: [
            "Les frais de livraison sont calculés automatiquement par Vinted selon ton adresse. [PACKAGE]",
            "Vinted calcule les frais d'envoi en fonction de ta localisation ! Tu verras le montant avant de valider.",
            "La livraison est gérée par Vinted, tu verras le prix exact au moment de l'achat. 😊"
        ],

        MessageType.SIZE_QUESTION: [
            "La taille est indiquée dans l'annonce : {size}. N'hésite pas si tu veux des mesures précises !",
            "C'est un {size} ! Je peux te donner les mesures exactes si besoin.",
            "Taille {size}, ça correspond à un {size} classique. 😊"
        ],

        MessageType.CONDITION_QUESTION: [
            "L'état est indiqué dans l'annonce ({condition}). Les photos montrent bien l'article !",
            "L'article est en {condition}. Tu peux zoomer sur les photos pour voir tous les détails. 😊",
            "Comme indiqué : {condition}. Si tu veux des photos supplémentaires, dis-moi ! [PHOTO]"
        ],

        MessageType.THANK_YOU: [
            "De rien ! 😊",
            "Avec plaisir ! N'hésite pas si tu as d'autres questions.",
            "Pas de souci ! Bonne journée ! ☀️"
        ],

        MessageType.GREETING: [
            "Hello ! 👋 Comment puis-je t'aider ?",
            "Salut ! N'hésite pas si tu as des questions. 😊",
            "Bonjour ! Je suis là si tu as besoin d'infos. 👋"
        ]
    }

    @classmethod
    def get_template(cls, message_type: MessageType) -> Optional[str]:
        """Get random template for message type"""
        templates = cls.TEMPLATES.get(message_type)
        if templates:
            return random.choice(templates)
        return None


class AIResponseGenerator:
    """Generates AI-powered responses using GPT"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key

    async def generate_response(
        self,
        message_text: str,
        context: ConversationContext,
        tone: ResponseTone = ResponseTone.FRIENDLY
    ) -> str:
        """
        Generate AI response using GPT

        Args:
            message_text: Incoming message
            context: Conversation context
            tone: Desired response tone

        Returns:
            Generated response text
        """
        if not self.api_key:
            logger.warning("No OpenAI API key, using template")
            return self._fallback_template_response(message_text, context)

        try:
            # Build prompt
            system_prompt = self._build_system_prompt(tone, context)
            user_prompt = f"Message du client : \"{message_text}\"\n\nRéponds de manière naturelle et utile."

            # Call GPT-4
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )

            reply = response.choices[0].message.content.strip()
            logger.info(f"Generated AI response: {reply[:50]}...")

            return reply

        except Exception as e:
            logger.error(f"GPT generation failed: {e}")
            return self._fallback_template_response(message_text, context)

    def _build_system_prompt(self, tone: ResponseTone, context: ConversationContext) -> str:
        """Build system prompt for GPT"""
        tone_instructions = {
            ResponseTone.FRIENDLY: "Tu es amical(e), utilise des emojis, sois chaleureux/se mais professionnel(le).",
            ResponseTone.PROFESSIONAL: "Tu es poli(e) et formel(le), pas d'emojis, reste professionnel(le).",
            ResponseTone.CONCISE: "Réponds de manière courte et directe, maximum 2 phrases.",
            ResponseTone.ENTHUSIASTIC: "Tu es enthousiaste et serviable, utilise des emojis et montre de l'énergie !"
        }

        item_info = ""
        if context.item_title:
            item_info = f"\n- Article concerné : {context.item_title}"
        if context.item_price:
            item_info += f"\n- Prix : {context.item_price}€"

        return f"""Tu es un vendeur Vinted qui répond aux messages des acheteurs.

{tone_instructions[tone]}

Contexte :
- Tu vends des articles sur Vinted{item_info}
- Réponds toujours en français
- Sois honnête et transparent
- Si on te demande de baisser le prix, reste ferme mais poli
- Si on demande si c'est disponible, confirme que oui
- Maximum 2-3 phrases

NE JAMAIS :
- Donner ton numéro de téléphone
- Proposer une transaction hors Vinted
- Accepter des prix trop bas
- Être impoli ou négatif"""

    def _fallback_template_response(
        self,
        message_text: str,
        context: ConversationContext
    ) -> str:
        """Fallback to template if GPT fails"""
        message_type = MessageClassifier.classify(message_text)
        template = TemplateLibrary.get_template(message_type)

        if template:
            # Fill in variables if available
            try:
                return template.format(
                    size="M",  # Default, should come from context
                    condition="Bon état",  # Default
                    price=context.item_price or "XX"
                )
            except KeyError:
                return template

        # Generic fallback
        return "Merci pour ton message ! Je reviens vers toi très vite. 😊"


class AutoMessagesService:
    """
    AI-Powered Auto-Messages Service

    Features:
    - Automatic message classification
    - Template-based quick responses
    - GPT-4 powered intelligent replies
    - Conversation context tracking
    - Rate limiting to avoid spam
    - Manual override capability
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.enabled = False
        self.tone = ResponseTone.FRIENDLY
        self.ai_generator = AIResponseGenerator()
        self.contexts: Dict[str, ConversationContext] = {}
        self.running = False

        # Settings
        self.auto_reply_delay_seconds = (30, 120)  # Random delay before replying
        self.max_auto_replies_per_conversation = 2  # Limit auto-replies per convo

    def enable(
        self,
        tone: ResponseTone = ResponseTone.FRIENDLY,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """Enable auto-messages"""
        self.enabled = True
        self.tone = tone
        self.use_ai = use_ai

        logger.info(f"[OK] Auto-messages enabled (tone: {tone.value}, AI: {use_ai})")

        return {
            'success': True,
            'enabled': True,
            'tone': tone.value,
            'ai_enabled': use_ai
        }

    def disable(self) -> Dict[str, Any]:
        """Disable auto-messages"""
        self.enabled = False
        logger.info("Auto-messages disabled")

        return {
            'success': True,
            'enabled': False
        }

    async def process_incoming_message(
        self,
        conversation_id: str,
        message_text: str,
        sender_id: str,
        sender_username: str,
        item_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Process an incoming message and generate auto-reply if enabled

        Args:
            conversation_id: Conversation ID
            message_text: Message content
            sender_id: Sender user ID
            sender_username: Sender username
            item_id: Related item ID

        Returns:
            Generated reply or None if auto-reply not triggered
        """
        if not self.enabled:
            return None

        # Get or create context
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = ConversationContext(
                conversation_id=conversation_id,
                other_user_id=sender_id,
                other_username=sender_username,
                item_id=item_id
            )

        context = self.contexts[conversation_id]
        context.message_count += 1
        context.last_message_at = datetime.now()

        # Check if we should auto-reply
        if context.message_count > self.max_auto_replies_per_conversation:
            logger.info(f"Max auto-replies reached for conversation {conversation_id}")
            return None

        # Classify message
        message_type = MessageClassifier.classify(message_text)
        logger.info(f"Classified message as: {message_type.value}")

        # Generate response
        if self.use_ai and self.ai_generator.api_key:
            reply = await self.ai_generator.generate_response(
                message_text,
                context,
                self.tone
            )
        else:
            # Use template
            template = TemplateLibrary.get_template(message_type)
            reply = template if template else "Merci pour ton message ! 😊"

        logger.info(f"Generated reply: {reply[:50]}...")

        return reply

    async def send_auto_reply(
        self,
        conversation_id: str,
        reply_text: str
    ) -> bool:
        """Send auto-reply to conversation"""

        # Human-like delay before replying
        delay = random.randint(*self.auto_reply_delay_seconds)
        logger.info(f"Waiting {delay}s before sending reply...")
        await asyncio.sleep(delay)

        # Get session
        session = _session(self.user_id)
        if not session:
            logger.error("No Vinted session")
            return False

        # Send message
        async with VintedAPIClient(session=session) as client:
            success, error = await client.send_message(conversation_id, reply_text)

            if success:
                logger.info(f"[OK] Auto-reply sent to conversation {conversation_id}")

                # Mark context as auto-replied
                if conversation_id in self.contexts:
                    self.contexts[conversation_id].auto_replied = True

                return True
            else:
                logger.error(f"[ERROR] Failed to send auto-reply: {error}")
                return False

    async def run_message_monitor(self):
        """
        Background task to monitor and respond to messages

        Usage:
            asyncio.create_task(service.run_message_monitor())
        """
        logger.info(f"[START] Auto-messages monitor started for user {self.user_id}")
        self.running = True

        while self.running:
            try:
                if not self.enabled:
                    await asyncio.sleep(60)
                    continue

                # Get session
                session = get_vinted_session(self.user_id)
                if not session:
                    await asyncio.sleep(60)
                    continue

                # Fetch new messages
                async with VintedAPIClient(session=session) as client:
                    success, conversations, error = await client.get_conversations()

                    if not success:
                        logger.error(f"Failed to fetch conversations: {error}")
                        await asyncio.sleep(60)
                        continue

                    # Process unread conversations
                    for convo in conversations:
                        convo_id = str(convo.get('id'))

                        # Check if has unread messages
                        if convo.get('unread_count', 0) == 0:
                            continue

                        # Get latest message
                        messages = convo.get('messages', [])
                        if not messages:
                            continue

                        latest_message = messages[-1]

                        # Check if message is from other user (not from us)
                        if latest_message.get('user_id') == self.user_id:
                            continue

                        # Process and reply
                        reply = await self.process_incoming_message(
                            conversation_id=convo_id,
                            message_text=latest_message.get('body', ''),
                            sender_id=str(latest_message.get('user_id')),
                            sender_username=latest_message.get('user', {}).get('login', 'User'),
                            item_id=str(convo.get('item', {}).get('id')) if convo.get('item') else None
                        )

                        if reply:
                            await self.send_auto_reply(convo_id, reply)

                # Check every 2 minutes
                await asyncio.sleep(120)

            except Exception as e:
                logger.error(f"Error in message monitor: {e}")
                await asyncio.sleep(60)

    def stop(self):
        """Stop message monitor"""
        logger.info("Stopping auto-messages monitor...")
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'enabled': self.enabled,
            'running': self.running,
            'tone': self.tone.value if self.enabled else None,
            'ai_enabled': self.use_ai if self.enabled else None,
            'active_conversations': len(self.contexts),
            'total_auto_replies': sum(
                1 for ctx in self.contexts.values() if ctx.auto_replied
            )
        }


# Global service instances
_auto_message_services: Dict[int, AutoMessagesService] = {}


def get_auto_messages_service(user_id: int) -> AutoMessagesService:
    """Get or create auto-messages service for user"""
    if user_id not in _auto_message_services:
        _auto_message_services[user_id] = AutoMessagesService(user_id)
    return _auto_message_services[user_id]
