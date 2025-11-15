"""
OpenAI Client Wrapper with Timeout Protection

Prevents server freezes from hanging OpenAI API calls.

All calls automatically timeout after 30 seconds to prevent:
- Server hangs from slow OpenAI responses
- Resource exhaustion from stuck requests
- Cascade failures from blocked threads
"""
import asyncio
import logging
from typing import Any, Optional
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)

# Timeout configuration
OPENAI_TIMEOUT = 30  # 30 seconds max for any OpenAI API call


class TimeoutOpenAIClient:
    """
    OpenAI client wrapper with automatic timeout protection

    Usage:
        client = TimeoutOpenAIClient()
        response = await client.chat.completions.create(...)
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = OPENAI_TIMEOUT):
        """
        Initialize OpenAI client with timeout protection

        Args:
            api_key: OpenAI API key (defaults to env var)
            timeout: Timeout in seconds (default: 30s)
        """
        self.timeout = timeout
        api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.warning("OPENAI_API_KEY not set - AI features will not work")
            self._client = None
        else:
            self._client = AsyncOpenAI(api_key=api_key)

    @property
    def is_configured(self) -> bool:
        """Check if client is properly configured"""
        return self._client is not None

    async def _call_with_timeout(self, coroutine):
        """
        Execute an async function with timeout protection

        Raises:
            asyncio.TimeoutError: If call exceeds timeout
            Exception: Any other error from the API call
        """
        try:
            return await asyncio.wait_for(coroutine, timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.error(f"OpenAI API call timed out after {self.timeout}s")
            raise asyncio.TimeoutError(f"OpenAI API call exceeded {self.timeout}s timeout")

    class ChatCompletions:
        """Chat completions endpoint with timeout"""

        def __init__(self, parent):
            self.parent = parent

        async def create(self, **kwargs):
            """
            Create chat completion with timeout protection

            Args:
                **kwargs: Arguments passed to OpenAI API

            Returns:
                OpenAI chat completion response

            Raises:
                asyncio.TimeoutError: If call exceeds 30s
                ValueError: If client not configured
            """
            if not self.parent._client:
                raise ValueError("OpenAI client not configured - OPENAI_API_KEY not set")

            logger.debug(f"OpenAI API call: model={kwargs.get('model')}, timeout={self.parent.timeout}s")

            return await self.parent._call_with_timeout(
                self.parent._client.chat.completions.create(**kwargs)
            )

    @property
    def chat(self):
        """Access chat endpoint"""
        return type('Chat', (), {'completions': self.ChatCompletions(self)})()


# Global shared client instance
_global_client: Optional[TimeoutOpenAIClient] = None


def get_openai_client() -> TimeoutOpenAIClient:
    """
    Get global OpenAI client instance with timeout protection

    Returns:
        TimeoutOpenAIClient instance
    """
    global _global_client
    if _global_client is None:
        _global_client = TimeoutOpenAIClient()
        logger.info(f"OpenAI client initialized with {OPENAI_TIMEOUT}s timeout")
    return _global_client
