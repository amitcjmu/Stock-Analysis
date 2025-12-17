"""
Multi-Model Service for handling different LLMs for different use cases.
- Llama 4 Maverick: Complex agentic tasks, CMDB analysis, field mapping (uses CrewAI wrapper)
- Gemma 3 4B: Chat interactions, simple queries, cost-efficient operations (uses OpenAI interface)
"""

import asyncio
import concurrent.futures
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config import settings

# Import LLM Usage Tracker
from app.services.llm_usage_tracker import llm_tracker

LLM_TRACKING_AVAILABLE = True  # Enable automatic LLM usage tracking

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI client not available for Gemma-3.")

try:
    from crewai import LLM

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logging.warning("CrewAI not available for Llama 4.")

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI SDK not available for Gemini.")

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available model types for different use cases."""

    LLAMA_4_MAVERICK = "llama4_maverick"
    GEMMA_3_4B = "gemma3_4b"
    GEMINI = "gemini"
    AUTO = "auto"


class TaskComplexity(Enum):
    """Task complexity levels for model selection."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    AGENTIC = "agentic"


class MultiModelService:
    """Service for managing multiple LLMs optimized for different tasks."""

    def __init__(self):
        self.openai_client = None  # For Gemma-3
        self.crewai_llm = None  # For Llama 4
        self.gemini_client = None  # For Google Gemini
        self.llm_usage_tracker = llm_tracker  # Use global tracker instance
        self.model_configs = {
            ModelType.LLAMA_4_MAVERICK: {
                "model_name": "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                "temperature": 0.0,
                "max_tokens": 1500,
                "top_p": 0.1,
                "use_cases": [
                    "agentic",
                    "complex_analysis",
                    "field_mapping",
                    "learning",
                ],
                "interface": "crewai",
            },
            ModelType.GEMMA_3_4B: {
                "model_name": "google/gemma-3-4b-it",
                "temperature": 0.7,  # Higher temperature for chat
                "max_tokens": 1000,
                "top_p": 0.9,
                "use_cases": ["chat", "simple_queries", "multimodal", "cost_efficient"],
                "interface": "openai",
            },
            ModelType.GEMINI: {
                "model_name": settings.GEMINI_MODEL,
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.95,
                "use_cases": [
                    "agentic",
                    "complex_analysis",
                    "multimodal",
                    "reasoning",
                    "stock_analysis",
                ],
                "interface": "gemini",
            },
        }

        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize OpenAI client for Gemma-3, CrewAI LLM for Llama 4, and Gemini client."""

        # Initialize OpenAI client for Gemma-3 (works well with OpenAI interface)
        if OPENAI_AVAILABLE and settings.DEEPINFRA_API_KEY:
            try:
                self.openai_client = OpenAI(
                    base_url="https://api.deepinfra.com/v1/openai",
                    api_key=settings.DEEPINFRA_API_KEY,
                )
                logger.info("Initialized OpenAI client for Gemma-3 4B")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client for Gemma-3: {e}")
                self.openai_client = None

        # Initialize CrewAI LLM for Llama 4 (uses existing wrapper due to compatibility issues)
        if CREWAI_AVAILABLE and settings.DEEPINFRA_API_KEY:
            try:
                llama_config = self.model_configs[ModelType.LLAMA_4_MAVERICK]
                self.crewai_llm = LLM(
                    model=llama_config["model_name"],
                    api_key=settings.DEEPINFRA_API_KEY,
                    temperature=llama_config["temperature"],
                    max_tokens=llama_config["max_tokens"],
                    top_p=llama_config["top_p"],
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                )
                logger.info("Initialized CrewAI LLM for Llama 4 Maverick")
            except Exception as e:
                logger.error(f"Failed to initialize CrewAI LLM for Llama 4: {e}")
                self.crewai_llm = None

        # Initialize Google Gemini client
        if GEMINI_AVAILABLE and settings.GOOGLE_GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

                # Try to list available models to find the correct name
                try:
                    available_models = list(genai.list_models())
                    model_names = [
                        m.name
                        for m in available_models
                        if "generateContent" in m.supported_generation_methods
                    ]
                    logger.info(f"Available Gemini models: {model_names}")

                    # Try to find a matching model or use a fallback
                    model_name = settings.GEMINI_MODEL

                    # Check if the configured model is available (with or without prefix)
                    if (
                        model_name not in model_names
                        and f"models/{model_name}" not in model_names
                    ):
                        # Try common alternatives in order of preference
                        alternatives = [
                            "gemini-2.5-flash",  # Latest fast model
                            "gemini-2.5-pro",  # Latest pro model
                            "gemini-2.0-flash",  # Stable 2.0 version
                            "gemini-pro-latest",  # Stable pro version
                            "gemini-flash-latest",  # Latest flash
                        ]
                        for alt in alternatives:
                            # Check both with and without models/ prefix
                            if f"models/{alt}" in model_names:
                                model_name = alt  # Use without prefix (API handles it)
                                logger.info(f"Using alternative model: {model_name}")
                                break
                        else:
                            # Use first available model that supports generateContent
                            if model_names:
                                # Remove 'models/' prefix for the model name
                                model_name = model_names[0].replace("models/", "")
                                logger.warning(
                                    f"Model {settings.GEMINI_MODEL} not found, using: {model_name}"
                                )
                except Exception as list_error:
                    logger.warning(
                        f"Could not list models, using configured name: {list_error}"
                    )
                    model_name = settings.GEMINI_MODEL

                self.gemini_client = genai.GenerativeModel(model_name)
                logger.info(f"Initialized Google Gemini client for {model_name}")
            except Exception as e:
                logger.error(
                    f"Failed to initialize Google Gemini client: {e}", exc_info=True
                )
                self.gemini_client = None
        else:
            if not GEMINI_AVAILABLE:
                logger.warning("Google Generative AI SDK not available")
            if not settings.GOOGLE_GEMINI_API_KEY:
                logger.warning("GOOGLE_GEMINI_API_KEY not set")

        # Log initialization status
        available_models = []
        if self.openai_client:
            available_models.append("Gemma-3")
        if self.crewai_llm:
            available_models.append("Llama 4")
        if self.gemini_client:
            available_models.append("Gemini")

        if not available_models:
            logger.warning("Multi-model service initialized in placeholder mode")
        else:
            logger.info(
                f"Multi-model service initialized with: {', '.join(available_models)}"
            )

    def select_model(
        self, task_type: str, complexity: TaskComplexity = TaskComplexity.MEDIUM
    ) -> ModelType:
        """Intelligently select the best model for a given task."""

        # Agentic tasks always use Llama 4 Maverick
        agentic_tasks = [
            "cmdb_analysis",
            "field_mapping",
            "user_feedback",
            "complex_reasoning",
            "asset_classification",
            "dependency_analysis",
            "risk_assessment",
        ]

        # Chat and simple tasks use Gemma 3 4B
        chat_tasks = [
            "chat",
            "simple_query",
            "conversation",
            "basic_question",
            "quick_info",
            "help",
            "multimodal",
        ]

        if task_type in agentic_tasks or complexity == TaskComplexity.AGENTIC:
            return ModelType.LLAMA_4_MAVERICK
        elif task_type in chat_tasks or complexity == TaskComplexity.SIMPLE:
            return ModelType.GEMMA_3_4B
        else:
            # For medium complexity, choose based on specific task characteristics
            if "analysis" in task_type.lower() or "complex" in task_type.lower():
                return ModelType.LLAMA_4_MAVERICK
            else:
                return ModelType.GEMMA_3_4B

    async def generate_response(
        self,
        prompt: str,
        task_type: str = "general",
        model_type: Optional[ModelType] = None,
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        system_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a response using the appropriate model and interface."""

        # Select model if not specified
        if model_type is None:
            model_type = self.select_model(task_type, complexity)
            logger.info(
                f"🤖 Auto-selected model: {model_type.value} for task_type={task_type}, complexity={complexity.value}"
            )
        else:
            logger.info(f"🤖 Using explicitly selected model: {model_type.value}")

        # Get model configuration
        model_config = self.model_configs[model_type]
        interface = model_config["interface"]
        logger.info(
            f"🤖 Routing to interface: {interface} for model: {model_type.value}"
        )

        # Route to appropriate interface
        if interface == "openai" and model_type == ModelType.GEMMA_3_4B:
            return await self._generate_with_openai(
                prompt, model_type, system_message, task_type
            )
        elif interface == "crewai" and model_type == ModelType.LLAMA_4_MAVERICK:
            return await self._generate_with_crewai(
                prompt, model_type, system_message, task_type
            )
        elif interface == "gemini" and model_type == ModelType.GEMINI:
            return await self._generate_with_gemini(
                prompt, model_type, system_message, task_type
            )
        else:
            return self._placeholder_response(
                prompt,
                task_type,
                f"Interface {interface} not available for {model_type.value}",
            )

    async def _generate_with_openai(
        self,
        prompt: str,
        model_type: ModelType,
        system_message: Optional[str],
        task_type: str,
    ) -> Dict[str, Any]:
        """Generate response using OpenAI interface (for Gemma-3)."""

        if not self.openai_client:
            return self._placeholder_response(
                prompt, task_type, "OpenAI client not available"
            )

        model_config = self.model_configs[model_type]

        # Use LLM tracking if available
        if LLM_TRACKING_AVAILABLE:
            async with self.llm_usage_tracker.track_llm_call(
                provider="deepinfra",
                model=model_config["model_name"],
                feature_context=task_type,
                metadata={"interface": "openai", "model_type": model_type.value},
            ) as usage_log:
                return await self._execute_openai_call(
                    model_config,
                    prompt,
                    system_message,
                    task_type,
                    model_type,
                    usage_log,
                )
        else:
            return await self._execute_openai_call(
                model_config, prompt, system_message, task_type, model_type, None
            )

    async def _execute_openai_call(
        self,
        model_config,
        prompt,
        system_message,
        task_type,
        model_type,
        usage_log=None,
    ):
        """Execute the actual OpenAI API call with optional tracking."""
        try:
            # Prepare messages for OpenAI chat format
            messages = []

            # Add system message
            if system_message is None:
                system_message = (
                    "You are a helpful AI assistant. Provide clear, concise, "
                    "and friendly responses to user questions."
                )

            messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            # Store request data for tracking if available
            if usage_log:
                usage_log.request_data = {
                    "messages": [
                        {
                            "role": msg["role"],
                            "content": (
                                msg["content"][:200] + "..."
                                if len(msg["content"]) > 200
                                else msg["content"]
                            ),
                        }
                        for msg in messages
                    ],
                    "model": model_config["model_name"],
                    "temperature": model_config["temperature"],
                    "max_tokens": model_config["max_tokens"],
                }

            # Generate response using OpenAI client
            def generate():
                try:
                    completion = self.openai_client.chat.completions.create(
                        model=model_config["model_name"],
                        messages=messages,
                        temperature=model_config["temperature"],
                        max_tokens=model_config["max_tokens"],
                        top_p=model_config["top_p"],
                    )

                    response_content = completion.choices[0].message.content

                    # Calculate token usage
                    usage = completion.usage
                    tokens_used = usage.total_tokens if usage else 0

                    return {
                        "content": response_content,
                        "tokens_used": tokens_used,
                        "prompt_tokens": usage.prompt_tokens if usage else 0,
                        "completion_tokens": usage.completion_tokens if usage else 0,
                        "usage": usage,
                    }

                except Exception as e:
                    logger.error(f"OpenAI client error: {e}")
                    return {
                        "content": f"Chat response for: {prompt[:50]}... (fallback due to client error)",
                        "tokens_used": 0,
                        "error": str(e),
                    }

            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, generate)

            # Update usage tracking if available
            if usage_log and result.get("usage"):
                usage_log.input_tokens = result["prompt_tokens"]
                usage_log.output_tokens = result["completion_tokens"]
                usage_log.total_tokens = result["tokens_used"]
                usage_log.response_data = {
                    "content": (
                        result["content"][:200] + "..."
                        if len(result["content"]) > 200
                        else result["content"]
                    ),
                    "finish_reason": "stop",
                }

            return {
                "status": "success",
                "response": result["content"],
                "model_used": model_type.value,
                "task_type": task_type,
                "interface": "openai",
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": result["tokens_used"],
                "prompt_tokens": result.get("prompt_tokens", 0),
                "completion_tokens": result.get("completion_tokens", 0),
                "model_config": model_config,
                "usage_log_id": str(usage_log.id) if usage_log else None,
            }

        except Exception as e:
            logger.error(f"Error generating response with OpenAI interface: {e}")
            return {
                "status": "error",
                "error": str(e),
                "model_used": model_type.value,
                "interface": "openai",
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _generate_with_crewai(
        self,
        prompt: str,
        model_type: ModelType,
        system_message: Optional[str],
        task_type: str,
    ) -> Dict[str, Any]:
        """Generate response using CrewAI interface (for Llama 4)."""

        if not self.crewai_llm:
            return self._placeholder_response(
                prompt, task_type, "CrewAI LLM not available"
            )

        model_config = self.model_configs[model_type]

        # Use LLM tracking if available
        if LLM_TRACKING_AVAILABLE:
            async with self.llm_usage_tracker.track_llm_call(
                provider="deepinfra",
                model=model_config["model_name"],
                feature_context=task_type,
                metadata={"interface": "crewai", "model_type": model_type.value},
            ) as usage_log:
                return await self._execute_crewai_call(
                    model_config,
                    prompt,
                    system_message,
                    task_type,
                    model_type,
                    usage_log,
                )
        else:
            return await self._execute_crewai_call(
                model_config, prompt, system_message, task_type, model_type, None
            )

    async def _execute_crewai_call(
        self,
        model_config,
        prompt,
        system_message,
        task_type,
        model_type,
        usage_log=None,
    ):
        """Execute the actual CrewAI LLM call with optional tracking."""
        try:
            # Prepare the full prompt for CrewAI
            if system_message is None:
                system_message = (
                    "You are an expert AI assistant specialized in enterprise IT infrastructure "
                    "analysis and migration planning. Provide detailed, accurate, and actionable insights."
                )

            full_prompt = f"System: {system_message}\n\nTask: {prompt}\n\nProvide a comprehensive response:"

            # Store request data for tracking if available
            if usage_log:
                usage_log.request_data = {
                    "prompt": (
                        full_prompt[:500] + "..."
                        if len(full_prompt) > 500
                        else full_prompt
                    ),
                    "model": model_config["model_name"],
                    "temperature": model_config["temperature"],
                    "max_tokens": model_config["max_tokens"],
                }

            # Generate response using CrewAI LLM
            def generate():
                try:
                    # Use the correct method for LLM response generation
                    if hasattr(self.crewai_llm, "call"):
                        response = self.crewai_llm.call(full_prompt)
                    elif hasattr(self.crewai_llm, "invoke"):
                        response = self.crewai_llm.invoke(full_prompt)
                    elif hasattr(self.crewai_llm, "generate"):
                        response = self.crewai_llm.generate(full_prompt)
                    elif hasattr(self.crewai_llm, "__call__"):
                        response = self.crewai_llm(full_prompt)
                    else:
                        # Fallback for basic string generation
                        response = f"Response to: {full_prompt[:100]}... (generated by {model_type.value})"

                    response_str = str(response)
                    return {
                        "content": response_str,
                        "tokens_used": len(response_str.split()),  # Approximate
                        "input_tokens": len(full_prompt.split()),  # Approximate
                        "output_tokens": len(response_str.split()),  # Approximate
                    }

                except Exception as e:
                    logger.error(f"CrewAI LLM invocation failed: {e}")
                    return {
                        "content": f"Agentic response for: {prompt[:50]}... (fallback due to model error)",
                        "tokens_used": 0,
                        "error": str(e),
                    }

            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, generate)

            # Update usage tracking if available
            if usage_log:
                usage_log.input_tokens = result.get("input_tokens", 0)
                usage_log.output_tokens = result.get("output_tokens", 0)
                usage_log.total_tokens = result["tokens_used"]
                usage_log.response_data = {
                    "content": (
                        result["content"][:200] + "..."
                        if len(result["content"]) > 200
                        else result["content"]
                    ),
                    "interface": "crewai",
                }

            return {
                "status": "success",
                "response": result["content"],
                "model_used": model_type.value,
                "task_type": task_type,
                "interface": "crewai",
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": result["tokens_used"],
                "model_config": model_config,
                "usage_log_id": str(usage_log.id) if usage_log else None,
            }

        except Exception as e:
            logger.error(f"Error generating response with CrewAI interface: {e}")
            return {
                "status": "error",
                "error": str(e),
                "model_used": model_type.value,
                "interface": "crewai",
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _generate_with_gemini(
        self,
        prompt: str,
        model_type: ModelType,
        system_message: Optional[str],
        task_type: str,
    ) -> Dict[str, Any]:
        """Generate response using Google Gemini API."""

        logger.info(f"🔵 [GEMINI] Starting Gemini API call for task: {task_type}")

        if not self.gemini_client:
            logger.error("🔵 [GEMINI] Gemini client not available")
            return self._placeholder_response(
                prompt, task_type, "Gemini client not available"
            )

        model_config = self.model_configs[model_type]

        # Use LLM tracking if available
        if LLM_TRACKING_AVAILABLE:
            async with self.llm_usage_tracker.track_llm_call(
                provider="google",
                model=model_config["model_name"],
                feature_context=task_type,
                metadata={"interface": "gemini", "model_type": model_type.value},
            ) as usage_log:
                return await self._execute_gemini_call(
                    model_config,
                    prompt,
                    system_message,
                    task_type,
                    model_type,
                    usage_log,
                )
        else:
            return await self._execute_gemini_call(
                model_config, prompt, system_message, task_type, model_type, None
            )

    async def _execute_gemini_call(
        self,
        model_config,
        prompt,
        system_message,
        task_type,
        model_type,
        usage_log=None,
    ):
        """Execute the actual Gemini API call with optional tracking."""
        try:
            # Prepare the full prompt for Gemini
            if system_message is None:
                system_message = (
                    "You are an expert AI assistant specialized in stock market analysis "
                    "and financial insights. Provide detailed, accurate, and actionable insights."
                )

            # Combine system message and prompt
            full_prompt = f"{system_message}\n\n{prompt}"

            # Store request data for tracking if available
            if usage_log:
                usage_log.request_data = {
                    "prompt": (
                        full_prompt[:500] + "..."
                        if len(full_prompt) > 500
                        else full_prompt
                    ),
                    "model": model_config["model_name"],
                    "temperature": model_config["temperature"],
                    "max_tokens": model_config["max_tokens"],
                }

            # Generate response using Gemini
            def generate():
                try:
                    # Configure generation parameters
                    generation_config = {
                        "temperature": model_config["temperature"],
                        "top_p": model_config["top_p"],
                        "max_output_tokens": model_config["max_tokens"],
                    }

                    # Generate content
                    response = self.gemini_client.generate_content(
                        full_prompt,
                        generation_config=generation_config,
                    )

                    response_text = response.text if response.text else ""

                    # Try to get token usage from response
                    # Note: Gemini API may not always provide token counts
                    prompt_tokens = len(full_prompt.split())  # Approximate
                    completion_tokens = len(response_text.split())  # Approximate
                    total_tokens = prompt_tokens + completion_tokens

                    return {
                        "content": response_text,
                        "tokens_used": total_tokens,
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                    }

                except Exception as e:
                    logger.error(f"Gemini API call failed: {e}")
                    return {
                        "content": f"Gemini response for: {prompt[:50]}... (fallback due to API error)",
                        "tokens_used": 0,
                        "error": str(e),
                    }

            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, generate)

            # Update usage tracking if available
            if usage_log:
                usage_log.input_tokens = result.get("input_tokens", 0)
                usage_log.output_tokens = result.get("output_tokens", 0)
                usage_log.total_tokens = result["tokens_used"]
                usage_log.response_data = {
                    "content": (
                        result["content"][:200] + "..."
                        if len(result["content"]) > 200
                        else result["content"]
                    ),
                    "interface": "gemini",
                }

            return {
                "status": "success",
                "response": result["content"],
                "model_used": model_type.value,
                "task_type": task_type,
                "interface": "gemini",
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": result["tokens_used"],
                "prompt_tokens": result.get("input_tokens", 0),
                "completion_tokens": result.get("output_tokens", 0),
                "model_config": model_config,
                "usage_log_id": str(usage_log.id) if usage_log else None,
            }

        except Exception as e:
            logger.error(f"Error generating response with Gemini interface: {e}")
            return {
                "status": "error",
                "error": str(e),
                "model_used": model_type.value,
                "interface": "gemini",
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _placeholder_response(
        self, prompt: str, task_type: str, reason: str = "Service unavailable"
    ) -> Dict[str, Any]:
        """Placeholder response when models are not available."""
        return {
            "status": "placeholder",
            "response": f"Multi-model service unavailable ({reason}). For task '{task_type}': {prompt[:100]}...",
            "model_used": "placeholder",
            "task_type": task_type,
            "timestamp": datetime.utcnow().isoformat(),
            "note": reason,
        }

    async def chat_with_context(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle chat interactions with conversation context using Gemma-3."""

        # Build conversation context
        conversation_context = ""
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_context += f"{role.capitalize()}: {content}\n"

        # Add additional context if provided
        if context:
            conversation_context = f"Context: {context}\n\n{conversation_context}"

        # Prepare the chat prompt
        chat_prompt = f"{conversation_context}\nUser: {message}\n\nPlease provide a helpful response."

        # Use Gemma 3 4B for chat (OpenAI interface)
        return await self.generate_response(
            chat_prompt,
            task_type="chat",
            model_type=ModelType.GEMMA_3_4B,
            complexity=TaskComplexity.SIMPLE,
            system_message=(
                "You are a knowledgeable assistant helping with IT infrastructure "
                "and migration questions. Be conversational and helpful."
            ),
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models and their use cases."""
        return {
            "available_models": [model.value for model in self.model_configs.keys()],
            "model_configs": {k.value: v for k, v in self.model_configs.items()},
            "service_status": {
                "gemma_3_4b": "active" if self.openai_client else "unavailable",
                "llama_4_maverick": "active" if self.crewai_llm else "unavailable",
                "gemini": "active" if self.gemini_client else "unavailable",
                "overall": (
                    "active"
                    if (self.openai_client or self.crewai_llm or self.gemini_client)
                    else "unavailable"
                ),
            },
            "interfaces": {
                "gemma_3_4b": "OpenAI compatible (DeepInfra)",
                "llama_4_maverick": "CrewAI wrapper (DeepInfra)",
                "gemini": "Google Generative AI SDK",
            },
            "recommendations": {
                "agentic_tasks": ModelType.LLAMA_4_MAVERICK.value,
                "chat_interactions": ModelType.GEMMA_3_4B.value,
                "cost_optimization": ModelType.GEMMA_3_4B.value,
                "complex_analysis": ModelType.LLAMA_4_MAVERICK.value,
            },
        }


# Global instance of the service
multi_model_service = MultiModelService()
