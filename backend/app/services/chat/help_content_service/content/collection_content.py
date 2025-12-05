"""
Collection flow help content for contextual chat assistant.

Contains help articles related to the Collection workflow.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

from typing import Any, Dict, List

# Collection Flow Help Content
COLLECTION_CONTENT: List[Dict[str, Any]] = [
    {
        "title": "Adaptive Forms Guide",
        "slug": "collection-adaptive-forms",
        "content": """Adaptive Forms are intelligent questionnaires that gather additional application details.

**How Adaptive Forms Work:**
- Questions change based on previous answers
- Gap-based generation shows only what's missing
- Progress tracked per section and overall

**Question Types:**
- **Single Select**: Choose one option
- **Multiple Select**: Choose multiple options
- **Numeric Input**: Enter numbers
- **Boolean (Yes/No)**: Simple true/false
- **Text Input**: Detailed explanations
- **File Upload**: Supporting documents

**Best Practices:**
1. Answer all required questions (marked with *)
2. Provide accurate, data-driven responses
3. Include supporting documentation when available
4. Save progress frequently (auto-saves every 30 seconds)
5. Consult subject matter experts for technical questions

**Why Questions Change:**
The system uses intelligent gap analysis to:
- Skip questions for data you've already provided
- Ask follow-up questions based on previous answers
- Prioritize critical missing information
- Avoid redundant data collection""",
        "summary": "Complete intelligent questionnaires for detailed application data",
        "category": "collection",
        "flow_type": "collection",
        "route": "/collection/adaptive-forms",
        "tags": ["forms", "questionnaire", "questions", "data", "collection"],
        "faq_questions": [
            "Why do questions change based on answers?",
            "How do I save my progress?",
            "What if I don't know an answer?",
        ],
    },
]
