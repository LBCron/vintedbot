"""
Cost tracking system for OpenAI API usage
Track GPT-4 Vision costs per user and overall
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from loguru import logger
import json
from pathlib import Path


@dataclass
class GPTUsage:
    """GPT API usage record"""
    user_id: int
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    request_type: str  # "photo_analysis", "chat", etc.
    timestamp: datetime


class CostTracker:
    """
    Track and analyze OpenAI API costs

    Pricing (as of 2024):
    - GPT-4 Turbo: $0.01 / 1K prompt tokens, $0.03 / 1K completion tokens
    - GPT-4: $0.03 / 1K prompt tokens, $0.06 / 1K completion tokens
    - GPT-4o (Vision): $0.005 / 1K prompt tokens, $0.015 / 1K completion tokens
    - GPT-3.5 Turbo: $0.0005 / 1K prompt tokens, $0.0015 / 1K completion tokens
    """

    # Pricing per 1K tokens (USD)
    PRICING = {
        "gpt-4": {
            "prompt": 0.03,
            "completion": 0.06
        },
        "gpt-4-turbo": {
            "prompt": 0.01,
            "completion": 0.03
        },
        "gpt-4o": {  # GPT-4o (used for vision)
            "prompt": 0.005,
            "completion": 0.015
        },
        "gpt-3.5-turbo": {
            "prompt": 0.0005,
            "completion": 0.0015
        }
    }

    def __init__(self, storage_path: str = "backend/data/cost_tracking.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache for fast queries
        self.cache: Dict[int, List[GPTUsage]] = {}

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for API call

        Args:
            model: Model name (e.g., "gpt-4o", "gpt-4-turbo")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Cost in USD
        """
        # Normalize model name
        model_key = model.lower()
        if "gpt-4o" in model_key:
            model_key = "gpt-4o"
        elif "gpt-4-turbo" in model_key:
            model_key = "gpt-4-turbo"
        elif "gpt-4" in model_key:
            model_key = "gpt-4"
        elif "gpt-3.5" in model_key:
            model_key = "gpt-3.5-turbo"
        else:
            logger.warning(f"Unknown model: {model}, defaulting to gpt-4o pricing")
            model_key = "gpt-4o"

        pricing = self.PRICING.get(model_key, self.PRICING["gpt-4o"])

        cost = (
            (prompt_tokens / 1000) * pricing["prompt"] +
            (completion_tokens / 1000) * pricing["completion"]
        )

        return round(cost, 6)  # Round to 6 decimal places

    def track_usage(
        self,
        user_id: int,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        request_type: str = "general"
    ) -> GPTUsage:
        """
        Track API usage and cost

        Args:
            user_id: User ID
            model: Model used
            prompt_tokens: Prompt tokens
            completion_tokens: Completion tokens
            request_type: Type of request (e.g., "photo_analysis")

        Returns:
            GPTUsage record
        """
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = self.calculate_cost(model, prompt_tokens, completion_tokens)

        usage = GPTUsage(
            user_id=user_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            request_type=request_type,
            timestamp=datetime.now()
        )

        # Save to storage
        self._save_usage(usage)

        # Update cache
        if user_id not in self.cache:
            self.cache[user_id] = []
        self.cache[user_id].append(usage)

        logger.info(
            f"Cost tracked: User {user_id}, {model}, "
            f"{total_tokens} tokens, ${cost_usd:.4f}"
        )

        return usage

    def _save_usage(self, usage: GPTUsage):
        """Save usage record to JSONL file"""
        try:
            record = {
                "user_id": usage.user_id,
                "model": usage.model,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "cost_usd": usage.cost_usd,
                "request_type": usage.request_type,
                "timestamp": usage.timestamp.isoformat()
            }

            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record) + '\n')

        except Exception as e:
            logger.error(f"Failed to save cost tracking: {e}")

    def get_user_cost_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get cost summary for a user

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            Cost summary with totals and breakdowns
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Load usage from storage if not in cache
        if user_id not in self.cache:
            self._load_user_cache(user_id)

        user_usage = self.cache.get(user_id, [])

        # Filter by date range
        recent_usage = [
            u for u in user_usage
            if u.timestamp >= cutoff_date
        ]

        if not recent_usage:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_cost_usd": 0.0,
                "total_requests": 0,
                "total_tokens": 0,
                "by_request_type": {},
                "by_model": {}
            }

        # Calculate totals
        total_cost = sum(u.cost_usd for u in recent_usage)
        total_tokens = sum(u.total_tokens for u in recent_usage)

        # Break down by request type
        by_request_type = {}
        for usage in recent_usage:
            if usage.request_type not in by_request_type:
                by_request_type[usage.request_type] = {
                    "requests": 0,
                    "cost_usd": 0.0,
                    "tokens": 0
                }
            by_request_type[usage.request_type]["requests"] += 1
            by_request_type[usage.request_type]["cost_usd"] += usage.cost_usd
            by_request_type[usage.request_type]["tokens"] += usage.total_tokens

        # Break down by model
        by_model = {}
        for usage in recent_usage:
            if usage.model not in by_model:
                by_model[usage.model] = {
                    "requests": 0,
                    "cost_usd": 0.0,
                    "tokens": 0
                }
            by_model[usage.model]["requests"] += 1
            by_model[usage.model]["cost_usd"] += usage.cost_usd
            by_model[usage.model]["tokens"] += usage.total_tokens

        return {
            "user_id": user_id,
            "period_days": days,
            "total_cost_usd": round(total_cost, 4),
            "total_requests": len(recent_usage),
            "total_tokens": total_tokens,
            "average_cost_per_request": round(total_cost / len(recent_usage), 4),
            "by_request_type": by_request_type,
            "by_model": by_model
        }

    def get_global_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get global cost summary across all users

        Args:
            days: Number of days to look back

        Returns:
            Global cost summary
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Load all usage from storage
        all_usage = self._load_all_usage()

        # Filter by date range
        recent_usage = [
            u for u in all_usage
            if u.timestamp >= cutoff_date
        ]

        if not recent_usage:
            return {
                "period_days": days,
                "total_cost_usd": 0.0,
                "total_requests": 0,
                "total_users": 0
            }

        # Calculate totals
        total_cost = sum(u.cost_usd for u in recent_usage)
        unique_users = len(set(u.user_id for u in recent_usage))

        return {
            "period_days": days,
            "total_cost_usd": round(total_cost, 2),
            "total_requests": len(recent_usage),
            "total_users": unique_users,
            "average_cost_per_user": round(total_cost / unique_users, 4) if unique_users > 0 else 0,
            "average_cost_per_request": round(total_cost / len(recent_usage), 4)
        }

    def _load_user_cache(self, user_id: int):
        """Load usage for a specific user into cache"""
        all_usage = self._load_all_usage()
        self.cache[user_id] = [u for u in all_usage if u.user_id == user_id]

    def _load_all_usage(self) -> List[GPTUsage]:
        """Load all usage records from storage"""
        usage_records = []

        if not self.storage_path.exists():
            return usage_records

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        usage_records.append(GPTUsage(
                            user_id=record["user_id"],
                            model=record["model"],
                            prompt_tokens=record["prompt_tokens"],
                            completion_tokens=record["completion_tokens"],
                            total_tokens=record["total_tokens"],
                            cost_usd=record["cost_usd"],
                            request_type=record["request_type"],
                            timestamp=datetime.fromisoformat(record["timestamp"])
                        ))
        except Exception as e:
            logger.error(f"Failed to load cost tracking data: {e}")

        return usage_records

    def estimate_cost_for_photos(
        self,
        num_photos: int,
        model: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """
        Estimate cost for analyzing photos

        Args:
            num_photos: Number of photos
            model: Model to use

        Returns:
            Cost estimate
        """
        # Average tokens per photo analysis (based on empirical data)
        # Typically: ~1000 tokens for image + 500 for prompt + 200 for response
        avg_prompt_tokens_per_photo = 1500
        avg_completion_tokens_per_photo = 200

        total_prompt_tokens = num_photos * avg_prompt_tokens_per_photo
        total_completion_tokens = num_photos * avg_completion_tokens_per_photo

        estimated_cost = self.calculate_cost(
            model,
            total_prompt_tokens,
            total_completion_tokens
        )

        return {
            "num_photos": num_photos,
            "model": model,
            "estimated_prompt_tokens": total_prompt_tokens,
            "estimated_completion_tokens": total_completion_tokens,
            "estimated_cost_usd": round(estimated_cost, 4),
            "note": "This is an estimate. Actual cost may vary."
        }


# Global cost tracker instance
cost_tracker = CostTracker()
