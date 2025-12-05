"""
Help Content Service - RAG-based Help Document Retrieval

This service provides retrieval-augmented generation (RAG) capabilities
for the Contextual AI Chat Assistant by managing help documentation
and performing semantic search.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

import logging
from typing import Dict, List, Optional

from app.models.help_document import HelpSearchResult, HelpDocumentResponse

from .content import STATIC_HELP_CONTENT

logger = logging.getLogger(__name__)


class HelpContentService:
    """Service for managing and retrieving help documentation."""

    def __init__(self):
        """Initialize the help content service."""
        self.static_content = STATIC_HELP_CONTENT
        self._keyword_index: Dict[str, List[int]] = {}
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        """Build a keyword index for fast text search."""
        for idx, doc in enumerate(self.static_content):
            # Index title words
            for word in doc["title"].lower().split():
                if word not in self._keyword_index:
                    self._keyword_index[word] = []
                self._keyword_index[word].append(idx)

            # Index tags
            for tag in doc.get("tags", []):
                tag_lower = tag.lower()
                if tag_lower not in self._keyword_index:
                    self._keyword_index[tag_lower] = []
                self._keyword_index[tag_lower].append(idx)

            # Index FAQ questions
            for faq in doc.get("faq_questions", []):
                for word in faq.lower().split():
                    if len(word) > 3:  # Skip short words
                        if word not in self._keyword_index:
                            self._keyword_index[word] = []
                        self._keyword_index[word].append(idx)

    def search_by_keywords(
        self,
        query: str,
        flow_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> List[HelpSearchResult]:
        """
        Search help content by keywords.

        Args:
            query: Search query text
            flow_type: Optional filter by flow type
            category: Optional filter by category
            limit: Maximum results to return

        Returns:
            List of HelpSearchResult with relevance scores
        """
        query_words = query.lower().split()
        doc_scores: Dict[int, float] = {}

        # Score documents based on keyword matches
        for word in query_words:
            if word in self._keyword_index:
                for idx in self._keyword_index[word]:
                    doc_scores[idx] = doc_scores.get(idx, 0) + 1.0

            # Partial matches
            for indexed_word, indices in self._keyword_index.items():
                if word in indexed_word or indexed_word in word:
                    for idx in indices:
                        doc_scores[idx] = doc_scores.get(idx, 0) + 0.5

        # Apply filters and build results
        results: List[HelpSearchResult] = []
        for idx, score in sorted(doc_scores.items(), key=lambda x: -x[1]):
            doc = self.static_content[idx]

            # Apply filters
            if flow_type and doc.get("flow_type") != flow_type:
                continue
            if category and doc.get("category") != category:
                continue

            # Normalize score
            normalized_score = min(score / len(query_words), 1.0) if query_words else 0

            results.append(
                HelpSearchResult(
                    document=HelpDocumentResponse(
                        id=f"static-{idx}",
                        title=doc["title"],
                        slug=doc["slug"],
                        content=doc["content"],
                        summary=doc.get("summary"),
                        category=doc.get("category", "general"),
                        flow_type=doc.get("flow_type"),
                        route=doc.get("route"),
                        tags=doc.get("tags", []),
                        related_pages=doc.get("related_pages", []),
                        faq_questions=doc.get("faq_questions", []),
                    ),
                    relevance_score=normalized_score,
                    matched_content=self._extract_snippet(doc["content"], query),
                )
            )

            if len(results) >= limit:
                break

        return results

    def get_by_route(self, route: str) -> Optional[HelpDocumentResponse]:
        """
        Get help content for a specific page route.

        Args:
            route: The page route to get help for

        Returns:
            HelpDocumentResponse or None if not found
        """
        for idx, doc in enumerate(self.static_content):
            if doc.get("route") == route:
                return HelpDocumentResponse(
                    id=f"static-{idx}",
                    title=doc["title"],
                    slug=doc["slug"],
                    content=doc["content"],
                    summary=doc.get("summary"),
                    category=doc.get("category", "general"),
                    flow_type=doc.get("flow_type"),
                    route=doc.get("route"),
                    tags=doc.get("tags", []),
                    related_pages=doc.get("related_pages", []),
                    faq_questions=doc.get("faq_questions", []),
                )
        return None

    def get_by_flow_type(self, flow_type: str) -> List[HelpDocumentResponse]:
        """
        Get all help content for a specific flow type.

        Args:
            flow_type: The flow type (discovery, collection, etc.)

        Returns:
            List of HelpDocumentResponse for the flow type
        """
        results = []
        for idx, doc in enumerate(self.static_content):
            if doc.get("flow_type") == flow_type:
                results.append(
                    HelpDocumentResponse(
                        id=f"static-{idx}",
                        title=doc["title"],
                        slug=doc["slug"],
                        content=doc["content"],
                        summary=doc.get("summary"),
                        category=doc.get("category", "general"),
                        flow_type=doc.get("flow_type"),
                        route=doc.get("route"),
                        tags=doc.get("tags", []),
                        related_pages=doc.get("related_pages", []),
                        faq_questions=doc.get("faq_questions", []),
                    )
                )
        return results

    def get_context_for_chat(
        self,
        query: str,
        route: Optional[str] = None,
        flow_type: Optional[str] = None,
    ) -> str:
        """
        Get relevant help context for chat responses.

        Args:
            query: User's question
            route: Current page route
            flow_type: Current flow type

        Returns:
            Formatted context string for chat prompts
        """
        context_parts = []

        # Get route-specific help
        if route:
            route_help = self.get_by_route(route)
            if route_help:
                context_parts.append(
                    f"## Page Help: {route_help.title}\n{route_help.summary or route_help.content[:500]}"
                )

        # Search for relevant content
        search_results = self.search_by_keywords(query, flow_type=flow_type, limit=3)

        if search_results:
            context_parts.append("\n## Relevant Documentation:")
            for result in search_results:
                if result.relevance_score > 0.3:
                    content_preview = (
                        result.matched_content
                        or result.document.summary
                        or result.document.content[:300]
                    )
                    context_parts.append(
                        f"\n### {result.document.title}\n{content_preview}"
                    )

        return "\n".join(context_parts) if context_parts else ""

    def _extract_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """Extract a relevant snippet from content based on query."""
        query_words = query.lower().split()
        content_lower = content.lower()

        # Find first occurrence of any query word
        best_pos = len(content)
        for word in query_words:
            pos = content_lower.find(word)
            if pos != -1 and pos < best_pos:
                best_pos = pos

        if best_pos == len(content):
            # No match found, return start of content
            return (
                content[:max_length] + "..." if len(content) > max_length else content
            )

        # Extract snippet around the match
        start = max(0, best_pos - 50)
        end = min(len(content), best_pos + max_length - 50)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet


# Singleton instance
help_content_service = HelpContentService()
