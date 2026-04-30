"""
LLM gateway using Anthropic Claude only (Messages API).

All ``generate_response()`` traffic uses ``CLAUDE_OPUS_MODEL`` (default
``claude-opus-4-6``). Set ``ANTHROPIC_API_KEY`` for live completions; otherwise
placeholders are returned.

Legacy ``ModelType`` values (Gemini, Llama, Gemma) are accepted for import
compatibility but are mapped to Claude.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.llm_usage_tracker_service import llm_tracker

LLM_TRACKING_AVAILABLE = True

try:
    from anthropic import AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Active model is Claude only; other members are legacy aliases."""

    CLAUDE_OPUS_4_6 = "claude_opus_4_6"
    AUTO = "auto"
    LLAMA_4_MAVERICK = "llama4_maverick"
    GEMMA_3_4B = "gemma3_4b"
    GEMINI = "gemini"


class TaskComplexity(Enum):
    """Task complexity hint (ignored for routing; kept for call-site compatibility)."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    AGENTIC = "agentic"


_LEGACY_TYPES = frozenset(
    {
        ModelType.AUTO,
        ModelType.LLAMA_4_MAVERICK,
        ModelType.GEMMA_3_4B,
        ModelType.GEMINI,
    }
)


class MultiModelService:
    """Anthropic-only LLM service."""

    def __init__(self) -> None:
        self.anthropic_client: Optional[Any] = None
        self.llm_usage_tracker = llm_tracker
        self.model_configs = {
            ModelType.CLAUDE_OPUS_4_6: {
                "model_name": settings.CLAUDE_OPUS_MODEL,
                "temperature": 0.3,
                "max_tokens": 8192,
                "top_p": 1.0,
                "interface": "anthropic",
            },
        }
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        if ANTHROPIC_AVAILABLE and settings.ANTHROPIC_API_KEY:
            try:
                self.anthropic_client = AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                )
                logger.info(
                    "Initialized Anthropic client (%s)",
                    settings.CLAUDE_OPUS_MODEL,
                )
            except Exception as e:
                logger.error(
                    "Failed to initialize Anthropic client: %s", e, exc_info=True
                )
                self.anthropic_client = None
        elif not settings.ANTHROPIC_API_KEY:
            logger.warning(
                "ANTHROPIC_API_KEY not set — LLM calls return placeholders until configured"
            )

    def select_model(
        self, task_type: str, complexity: TaskComplexity = TaskComplexity.MEDIUM
    ) -> ModelType:
        """Always Claude (Anthropic)."""
        return ModelType.CLAUDE_OPUS_4_6

    def _resolve_model_type(self, model_type: Optional[ModelType]) -> ModelType:
        if model_type is None or model_type in _LEGACY_TYPES:
            return ModelType.CLAUDE_OPUS_4_6
        return ModelType.CLAUDE_OPUS_4_6

    async def generate_response(
        self,
        prompt: str,
        task_type: str = "general",
        model_type: Optional[ModelType] = None,
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        system_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a response via Anthropic Claude."""
        resolved = self._resolve_model_type(model_type)
        if model_type is not None and model_type != resolved:
            logger.info(
                "Anthropic-only routing: requested %s → using %s",
                model_type.value,
                resolved.value,
            )
        else:
            logger.info(
                "Using Anthropic model %s for task_type=%s complexity=%s",
                resolved.value,
                task_type,
                complexity.value,
            )

        return await self._generate_with_anthropic(
            prompt, resolved, system_message, task_type
        )

    @staticmethod
    def _anthropic_error_kind(exc: Exception) -> Optional[str]:
        """
        Classify Anthropic API failures for clearer logs and API responses.

        Returns ``insufficient_credits`` for known billing / balance errors.
        """
        parts: List[str] = [f"{type(exc).__name__} {exc!s}"]
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                parts.append(str(err.get("message", "")))
                parts.append(str(err.get("type", "")))
        combined = " ".join(parts).lower()
        if (
            "credit balance is too low" in combined
            or "too low to access the anthropic api" in combined
        ):
            return "insufficient_credits"
        return None

    @staticmethod
    def _anthropic_message_text(message: Any) -> str:
        parts: List[str] = []
        for block in getattr(message, "content", []) or []:
            if getattr(block, "type", None) == "text":
                parts.append(getattr(block, "text", "") or "")
        return "".join(parts)

    async def _generate_with_anthropic(
        self,
        prompt: str,
        model_type: ModelType,
        system_message: Optional[str],
        task_type: str,
    ) -> Dict[str, Any]:
        if not self.anthropic_client:
            return self._placeholder_response(
                prompt,
                task_type,
                "Anthropic client not available (set ANTHROPIC_API_KEY and install anthropic)",
            )

        model_config = self.model_configs[ModelType.CLAUDE_OPUS_4_6]
        api_model = model_config["model_name"]

        if LLM_TRACKING_AVAILABLE:
            async with self.llm_usage_tracker.track_llm_call(
                provider="anthropic",
                model=api_model,
                feature_context=task_type,
                metadata={"interface": "anthropic", "model_type": model_type.value},
            ) as usage_log:
                return await self._execute_anthropic_call(
                    model_config,
                    prompt,
                    system_message,
                    task_type,
                    model_type,
                    usage_log,
                )
        return await self._execute_anthropic_call(
            model_config,
            prompt,
            system_message,
            task_type,
            model_type,
            None,
        )

    async def _execute_anthropic_call(
        self,
        model_config: Dict[str, Any],
        prompt: str,
        system_message: Optional[str],
        task_type: str,
        model_type: ModelType,
        usage_log: Optional[Any] = None,
    ) -> Dict[str, Any]:
        try:
            if system_message is None:
                system_message = (
                    "You are a precise assistant. Use only facts supplied in the "
                    "user message unless the task clearly allows general knowledge."
                )

            if usage_log:
                usage_log.request_data = {
                    "prompt_preview": (
                        prompt[:500] + "..." if len(prompt) > 500 else prompt
                    ),
                    "model": model_config["model_name"],
                    "temperature": model_config["temperature"],
                    "max_tokens": model_config["max_tokens"],
                }

            message = await self.anthropic_client.messages.create(
                model=model_config["model_name"],
                max_tokens=int(model_config["max_tokens"]),
                temperature=float(model_config["temperature"]),
                top_p=float(model_config.get("top_p", 1.0)),
                system=system_message,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = self._anthropic_message_text(message)
            input_tokens = 0
            output_tokens = 0
            usage = getattr(message, "usage", None)
            if usage is not None:
                input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
                output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
            total_tokens = input_tokens + output_tokens

            if usage_log:
                usage_log.input_tokens = input_tokens
                usage_log.output_tokens = output_tokens
                usage_log.total_tokens = total_tokens
                usage_log.response_data = {
                    "content": (
                        response_text[:200] + "..."
                        if len(response_text) > 200
                        else response_text
                    ),
                    "interface": "anthropic",
                }

            return {
                "status": "success",
                "response": response_text,
                "model_used": model_type.value,
                "task_type": task_type,
                "interface": "anthropic",
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": total_tokens,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "model_config": model_config,
                "usage_log_id": str(usage_log.id) if usage_log else None,
            }

        except Exception as e:
            kind = self._anthropic_error_kind(e)
            if kind == "insufficient_credits":
                logger.warning("Anthropic request rejected (billing / credits): %s", e)
                user_message = (
                    "Anthropic declined the request: workspace credit balance is too low. "
                    "Add credits or review Plans & Billing at https://console.anthropic.com/settings/plans"
                )
            else:
                logger.error(
                    "Error generating response with Anthropic: %s", e, exc_info=True
                )
                user_message = str(e)
            payload: Dict[str, Any] = {
                "status": "error",
                "error": user_message,
                "model_used": model_type.value,
                "interface": "anthropic",
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
            if kind:
                payload["anthropic_error_kind"] = kind
            return payload

    def _placeholder_response(
        self, prompt: str, task_type: str, reason: str = "Service unavailable"
    ) -> Dict[str, Any]:
        # Keep ``response`` UI-safe: do not embed prompts (they appear in stock dashboards).
        user_message = (
            "AI is not available: Anthropic Claude is not configured. "
            "Set ANTHROPIC_API_KEY on the server and restart the backend."
        )
        return {
            "status": "placeholder",
            "response": user_message,
            "model_used": "placeholder",
            "task_type": task_type,
            "timestamp": datetime.utcnow().isoformat(),
            "note": reason,
            "debug_task_type": task_type,
            "debug_prompt_len": len(prompt),
        }

    async def chat_with_context(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        conversation_context = ""
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_context += f"{role.capitalize()}: {content}\n"

        if context:
            conversation_context = f"Context: {context}\n\n{conversation_context}"

        chat_prompt = f"{conversation_context}\nUser: {message}\n\nPlease provide a helpful response."

        return await self.generate_response(
            chat_prompt,
            task_type="chat",
            model_type=ModelType.CLAUDE_OPUS_4_6,
            complexity=TaskComplexity.SIMPLE,
            system_message=(
                "You are a knowledgeable assistant for IT infrastructure and "
                "migration planning. Be conversational and accurate."
            ),
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "available_models": [ModelType.CLAUDE_OPUS_4_6.value],
            "model_configs": {k.value: v for k, v in self.model_configs.items()},
            "service_status": {
                "claude_opus_4_6": "active" if self.anthropic_client else "unavailable",
                "overall": "active" if self.anthropic_client else "unavailable",
            },
            "interfaces": {
                "claude_opus_4_6": "Anthropic Messages API",
            },
            "recommendations": {
                "all_tasks": ModelType.CLAUDE_OPUS_4_6.value,
            },
        }


multi_model_service = MultiModelService()
