"""
Assessment flow help content for contextual chat assistant.

Contains help articles related to the Assessment workflow.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

from typing import Any, Dict, List

# Assessment Flow Help Content
ASSESSMENT_CONTENT: List[Dict[str, Any]] = [
    {
        "title": "6R Treatment Analysis Overview",
        "slug": "assessment-6r-overview",
        "content": """The 6R Treatment Analysis helps determine the best migration strategy for each application.

**The 6R Strategies:**

**Minimal Modernization:**
- **Rehost** (Lift and Shift): Move to cloud with minimal changes
- **Replatform**: Make minor optimizations during migration

**High Modernization:**
- **Refactor**: Modify architecture for cloud optimization
- **Rearchitect**: Significantly redesign architecture
- **Rewrite**: Build new cloud-native applications

**Non-Migration:**
- **Retire**: Decommission unneeded applications
- **Replace**: Use SaaS or cloud-native alternatives

**Analysis Process:**
1. Select application for analysis
2. Configure analysis parameters
3. Answer qualifying questions
4. Review AI recommendations
5. Accept or iterate on strategy

**Key Parameters:**
- Business Value (1-10)
- Technical Complexity (1-10)
- Migration Urgency (1-10)
- Compliance Requirements (1-10)
- Cost Sensitivity (1-10)
- Risk Tolerance (1-10)
- Innovation Priority (1-10)""",
        "summary": "AI-powered cloud migration strategy recommendations",
        "category": "assessment",
        "flow_type": "assessment",
        "route": "/assessment/overview",
        "tags": ["6r", "strategy", "migration", "rehost", "refactor", "analysis"],
        "faq_questions": [
            "What are the 6R strategies?",
            "How are recommendations calculated?",
            "What parameters affect the analysis?",
        ],
    },
    {
        "title": "Understanding 6R Confidence Scores",
        "slug": "assessment-confidence-scores",
        "content": """Confidence scores indicate how reliable the AI's migration strategy recommendation is.

**Confidence Levels:**

**High Confidence (80-100%)**
- Strong data quality and completeness
- Clear strategy differentiation
- Consistent parameter alignment
- Minimal conflicting factors
- **Action**: Safe to proceed with recommendation

**Medium Confidence (60-79%)**
- Good data quality with some gaps
- Moderate strategy differentiation
- Some parameter conflicts
- **Action**: Review recommendation, consider additional questions

**Low Confidence (40-59%)**
- Limited data quality or completeness
- Close strategy scores
- Significant parameter conflicts
- **Action**: Iterate with more data or adjusted parameters

**Very Low Confidence (0-39%)**
- Poor data quality
- Unclear strategy differentiation
- Major parameter inconsistencies
- **Action**: Gather more data before making decisions

**Improving Confidence:**
1. Complete all qualifying questions
2. Upload supporting documentation
3. Ensure application data is current
4. Involve subject matter experts""",
        "summary": "Understanding AI recommendation confidence levels",
        "category": "assessment",
        "flow_type": "assessment",
        "route": "/assessment/overview",
        "tags": ["confidence", "score", "reliability", "accuracy"],
        "faq_questions": [
            "What does confidence score mean?",
            "How can I improve confidence?",
            "Should I trust low confidence recommendations?",
        ],
    },
]
