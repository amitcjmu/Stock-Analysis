"""
Contextual Chat Service - AI Chat with Page Context Awareness

This service provides context-aware chat responses based on:
- Current page context (features, actions, help topics)
- Flow state context (flow ID, phase, progress)
- RAG-retrieved help documentation
- Page-specific system prompts

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

import logging
from datetime import datetime
from typing import List, Optional

from app.services.multi_model_service import multi_model_service
from app.services.chat.help_content_service import help_content_service

from .models import (
    ContextualChatRequest,
    ContextualChatResponse,
    PageContext,
    FlowContext,
)
from .prompts import (
    BASE_SYSTEM_PROMPT,
    FLOW_TYPE_PROMPTS,
    PAGE_SPECIFIC_PROMPTS,
    GUIDED_WORKFLOW_PROMPTS,
)

logger = logging.getLogger(__name__)


class ContextualChatService:
    """Service for handling context-aware chat interactions."""

    def __init__(self):
        """Initialize the contextual chat service."""
        self.base_prompt = BASE_SYSTEM_PROMPT
        self.flow_prompts = FLOW_TYPE_PROMPTS
        self.page_prompts = PAGE_SPECIFIC_PROMPTS
        self.guided_prompts = GUIDED_WORKFLOW_PROMPTS

    def _build_system_prompt(
        self,
        page_context: Optional[PageContext],
        flow_context: Optional[FlowContext],
    ) -> str:
        """Build a dynamic system prompt based on context."""
        prompt_parts = [self.base_prompt]

        # Add flow-type specific context
        if page_context and page_context.flow_type in self.flow_prompts:
            prompt_parts.append(self.flow_prompts[page_context.flow_type])

        # Add page-specific context
        if page_context and page_context.route in self.page_prompts:
            prompt_parts.append(self.page_prompts[page_context.route])

        # Add current page context
        if page_context:
            page_info = f"""
## Current Page: {page_context.page_name}
Route: {page_context.route}
Description: {page_context.description}

**Available Features:** {', '.join(page_context.features[:5]) if page_context.features else 'N/A'}
**Possible Actions:** {', '.join(page_context.actions[:5]) if page_context.actions else 'N/A'}
**Help Topics:** {', '.join(page_context.help_topics[:5]) if page_context.help_topics else 'N/A'}
"""
            prompt_parts.append(page_info)

            # Add workflow info if available
            if page_context.workflow:
                workflow_info = f"""
**Workflow Status:**
- Current Phase: {page_context.workflow.phase}
- Step {page_context.workflow.step} of {page_context.workflow.total_steps}
- Next: {page_context.workflow.next_step or 'Complete'}
"""
                prompt_parts.append(workflow_info)

            # Add tips if available
            if page_context.tips:
                tips_info = f"""
**Tips for this page:**
{chr(10).join('- ' + tip for tip in page_context.tips[:3])}
"""
                prompt_parts.append(tips_info)

        # Add flow state context if available
        if flow_context and flow_context.flow_id:
            flow_info = f"""
## Active Flow Information
- Flow ID: {flow_context.flow_id[:8]}...
- Flow Type: {flow_context.flow_type or 'Unknown'}
- Current Phase: {flow_context.current_phase or 'Unknown'}
- Status: {flow_context.status or 'Unknown'}
- Progress: {flow_context.completion_percentage or 0}%
"""
            if flow_context.pending_actions:
                flow_info += (
                    f"- Pending Actions: {', '.join(flow_context.pending_actions[:3])}"
                )
            prompt_parts.append(flow_info)

            # Add guided workflow prompt if available for current phase
            if flow_context.flow_type and flow_context.current_phase:
                flow_type_prompts = self.guided_prompts.get(flow_context.flow_type, {})
                guided_prompt = flow_type_prompts.get(flow_context.current_phase)
                if guided_prompt:
                    prompt_parts.append(guided_prompt)

        return "\n".join(prompt_parts)

    def _get_suggested_actions(self, page_context: Optional[PageContext]) -> List[str]:
        """Get suggested actions based on current page."""
        if not page_context:
            return []

        suggestions = []

        # Add page actions
        suggestions.extend(page_context.actions[:3])

        # Add workflow-based suggestions
        if page_context.workflow:
            if page_context.workflow.next_step:
                suggestions.append(f"Proceed to {page_context.workflow.next_step}")

        return suggestions[:5]  # Limit to 5 suggestions

    def _get_related_help_topics(
        self, page_context: Optional[PageContext]
    ) -> List[str]:
        """Get related help topics for the current context."""
        if not page_context:
            return []

        topics = list(page_context.help_topics[:5])

        # Add feature-based topics
        for feature in page_context.features[:2]:
            topics.append(f"How to use {feature}")

        return topics[:7]  # Limit to 7 topics

    async def chat_with_context(
        self, request: ContextualChatRequest
    ) -> ContextualChatResponse:
        """
        Process a chat message with full page and flow context.

        Args:
            request: The contextual chat request with message and context

        Returns:
            ContextualChatResponse with response and metadata
        """
        try:
            logger.info(
                f"Processing contextual chat: {request.message[:50]}... "
                f"Page: {request.page_context.page_name if request.page_context else 'Unknown'}"
            )

            # Build dynamic system prompt
            system_prompt = self._build_system_prompt(
                request.page_context, request.flow_context
            )

            # Convert conversation history to dict format
            history = []
            if request.conversation_history:
                history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.conversation_history
                ]

            # Get RAG-retrieved help content based on the user's query
            help_context = help_content_service.get_context_for_chat(
                query=request.message,
                route=request.page_context.route if request.page_context else None,
                flow_type=(
                    request.page_context.flow_type if request.page_context else None
                ),
            )

            # Generate response using multi-model service
            # Include system prompt, help context, and breadcrumb
            full_context = (
                f"{system_prompt}\n\nBreadcrumb: {request.breadcrumb or 'N/A'}"
            )
            if help_context:
                full_context += f"\n\n{help_context}"

            result = await multi_model_service.chat_with_context(
                message=request.message,
                conversation_history=history,
                context=full_context,
            )

            # Build context summary for response
            context_used = {
                "page_name": (
                    request.page_context.page_name if request.page_context else None
                ),
                "route": request.page_context.route if request.page_context else None,
                "flow_type": (
                    request.page_context.flow_type if request.page_context else None
                ),
                "flow_id": (
                    request.flow_context.flow_id if request.flow_context else None
                ),
                "breadcrumb": request.breadcrumb,
                "system_prompt_length": len(system_prompt),
                "help_context_used": bool(help_context),
                "help_context_length": len(help_context) if help_context else 0,
            }

            if result.get("status") == "success":
                return ContextualChatResponse(
                    status="success",
                    response=result.get("response", ""),
                    model_used=result.get("model_used", "unknown"),
                    timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
                    context_used=context_used,
                    suggested_actions=self._get_suggested_actions(request.page_context),
                    related_help_topics=self._get_related_help_topics(
                        request.page_context
                    ),
                )
            else:
                return ContextualChatResponse(
                    status="error",
                    response=result.get(
                        "error", "Failed to generate response. Please try again."
                    ),
                    model_used=result.get("model_used", "unknown"),
                    timestamp=datetime.utcnow().isoformat(),
                    context_used=context_used,
                    suggested_actions=[],
                    related_help_topics=[],
                )

        except Exception as e:
            logger.error(f"Error in contextual chat: {e}")
            return ContextualChatResponse(
                status="error",
                response="I encountered an error processing your request. Please try again.",
                model_used="unknown",
                timestamp=datetime.utcnow().isoformat(),
                context_used={},
                suggested_actions=[],
                related_help_topics=[],
            )

    def get_page_greeting(self, page_context: Optional[PageContext]) -> str:
        """Generate a contextual greeting for the current page."""
        if not page_context:
            return (
                "Hello! I'm your AI migration assistant. "
                "How can I help you with your migration project today?"
            )

        greetings = {
            "discovery": (
                f"Welcome to {page_context.page_name}! I can help you with data "
                f"import, mapping, and quality analysis. What would you like to know?"
            ),
            "collection": (
                f"You're on {page_context.page_name}. I can assist with "
                f"questionnaires and data collection. How can I help?"
            ),
            "assessment": (
                f"Welcome to {page_context.page_name}! I can explain 6R strategies "
                f"and help with migration assessments. What do you need?"
            ),
            "planning": (
                f"You're in {page_context.page_name}. I can help with wave planning "
                f"and migration timelines. What's on your mind?"
            ),
            "decommission": (
                f"Welcome to {page_context.page_name}! I can guide you through "
                f"legacy system decommissioning. How can I assist?"
            ),
            "finops": (
                f"You're viewing {page_context.page_name}. I can help with cloud "
                f"costs and FinOps questions. What would you like to know?"
            ),
        }

        return greetings.get(
            page_context.flow_type,
            f"You're on {page_context.page_name}. How can I help you today?",
        )


# Singleton instance
contextual_chat_service = ContextualChatService()
