"""
Page-specific prompts for contextual chat service.

Contains detailed guidance prompts for specific pages within the application.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

from typing import Dict

# Page-specific prompts for detailed guidance
PAGE_SPECIFIC_PROMPTS: Dict[str, str] = {
    "/discovery/data-import": """
## Data Import Page
Help users import their CMDB or asset inventory data.

**Page Features:**
- Drag-and-drop file upload
- Support for CSV and Excel (.xlsx, .xls)
- AI-powered data analysis
- Preview of imported data

**How to Help:**
- Explain supported file formats (CSV, Excel)
- Guide through the upload process
- Explain what columns should be included
- Help troubleshoot upload errors
- Explain what happens after upload (AI analysis)

**Sample Questions Users Might Ask:**
- "What file format should I use?"
- "How large can my file be?"
- "What columns do I need?"
- "Why is my upload failing?"
""",
    "/discovery/attribute-mapping": """
## Attribute Mapping Page
Help users map their source fields to the target schema.

**Page Features:**
- AI-suggested mappings with confidence scores
- Three-column mapper (source → suggestion → target)
- Manual override capability
- Bulk approval of high-confidence mappings

**Confidence Score Guide:**
- Green (>80%): High confidence, likely correct
- Yellow (50-80%): Medium confidence, review recommended
- Red (<50%): Low confidence, needs manual review

**How to Help:**
- Explain what confidence scores mean
- Guide through manual override process
- Help with bulk approval decisions
- Explain what happens to unmapped fields
""",
    "/discovery/data-cleansing": """
## Data Cleansing Page
Help users resolve data quality issues identified by AI analysis.

**Issue Types:**
- Duplicates - Same asset appears multiple times
- Missing Values - Required fields are empty
- Invalid Formats - Data doesn't match expected format
- Inconsistencies - Values vary unexpectedly
- Anomalies - Outliers that may indicate errors

**How to Help:**
- Explain different issue types
- Guide through AI recommendations
- Help with manual data corrections
- Explain impact of unresolved issues
""",
    "/collection/adaptive-forms": """
## Adaptive Forms Page
Help users complete intelligent questionnaires.

**Page Features:**
- Dynamic questions based on previous answers
- Progress tracking per section
- Save and resume capability
- AI-assisted suggestions

**How to Help:**
- Explain why questions change based on answers
- Guide through saving progress
- Help with unclear questions
- Explain the importance of accurate data
""",
    "/assessment/overview": """
## Assessment Overview Page
Help users understand and manage their assessment flows.

**Page Features:**
- Assessment flow list
- Status tracking (Running, Completed, Failed)
- Quick actions (Continue, View Results)
- Summary metrics

**How to Help:**
- Explain assessment phases
- Guide through starting new assessments
- Help interpret status indicators
- Explain 6R recommendations
""",
    "/plan/waveplanning": """
## Wave Planning Page
Help users organize applications into migration waves.

**Page Features:**
- Drag-and-drop wave assignment
- Dependency visualization
- Conflict detection
- Wave timeline view

**How to Help:**
- Explain wave planning concepts
- Guide through creating waves
- Help resolve dependency conflicts
- Explain optimal wave ordering
""",
}
