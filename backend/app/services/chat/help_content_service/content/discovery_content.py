"""
Discovery flow help content for contextual chat assistant.

Contains help articles related to the Discovery workflow.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

from typing import Any, Dict, List

# Discovery Flow Help Content
DISCOVERY_CONTENT: List[Dict[str, Any]] = [
    {
        "title": "Data Import Overview",
        "slug": "discovery-data-import",
        "content": """Data Import is the first phase of the Discovery workflow.
Here you upload your CMDB or asset inventory data.

**Supported File Formats:**
- CSV files (.csv)
- Excel files (.xlsx, .xls)

**How to Import Data:**
1. Navigate to Discovery > Data Import
2. Drag and drop your file or click "Browse"
3. Preview the first 10 rows of your data
4. Verify column headers and data quality
5. Click "Import" to start AI analysis

**What Happens Next:**
- AI agents analyze your data structure
- Field mappings are automatically suggested
- Data quality issues are identified
- System prepares for the Attribute Mapping phase

**Common Issues:**
- Ensure your file has headers in the first row
- Check that the file is not password protected
- Verify the file size is under 50MB""",
        "summary": "Upload CMDB data via CSV or Excel for AI-powered analysis",
        "category": "discovery",
        "flow_type": "discovery",
        "route": "/discovery/data-import",
        "tags": ["import", "upload", "csv", "excel", "cmdb", "data"],
        "faq_questions": [
            "How do I import my CMDB data?",
            "What file formats are supported?",
            "Why is my upload failing?",
        ],
    },
    {
        "title": "Attribute Mapping Guide",
        "slug": "discovery-attribute-mapping",
        "content": """Attribute Mapping connects your source data fields to the target schema
using AI-assisted suggestions.

**Understanding Confidence Scores:**
- **Green (>80%)**: High confidence - likely correct, can be bulk approved
- **Yellow (50-80%)**: Medium confidence - review recommended
- **Red (<50%)**: Low confidence - needs manual review

**How to Map Attributes:**
1. Review AI-suggested mappings in the three-column view
2. Approve high-confidence mappings with bulk actions
3. Manually override incorrect suggestions
4. Mark unmapped fields as "Skip" if not needed

**Three-Column Mapper:**
- **Left**: Your source fields from the uploaded data
- **Center**: AI suggestion with confidence score
- **Right**: Target schema fields

**Best Practices:**
- Start by approving all high-confidence (green) mappings
- Focus on medium-confidence mappings next
- Document any custom mapping decisions
- Unmapped fields won't be processed in later phases""",
        "summary": "Map source fields to target schema with AI assistance",
        "category": "discovery",
        "flow_type": "discovery",
        "route": "/discovery/attribute-mapping",
        "tags": ["mapping", "fields", "schema", "ai", "confidence"],
        "faq_questions": [
            "What do confidence scores mean?",
            "How do I override AI suggestions?",
            "What happens to unmapped fields?",
        ],
    },
    {
        "title": "Data Cleansing Workflow",
        "slug": "discovery-data-cleansing",
        "content": """Data Cleansing helps you resolve data quality issues identified by AI analysis.

**Issue Types:**
- **Duplicates**: Same asset appears multiple times
- **Missing Values**: Required fields are empty
- **Invalid Formats**: Data doesn't match expected format
- **Inconsistencies**: Values vary unexpectedly
- **Anomalies**: Outliers that may indicate errors

**How to Resolve Issues:**
1. Review the list of identified issues
2. Accept AI recommendations to auto-fix
3. Or manually correct values
4. Mark false positives as "Ignore"

**Quality Score:**
The data quality score indicates overall data health:
- **>85%**: Good - ready for next phase
- **60-85%**: Fair - some issues should be addressed
- **<60%**: Poor - significant cleanup needed

**Impact of Unresolved Issues:**
- Duplicate assets may cause incorrect dependency mapping
- Missing values reduce AI recommendation accuracy
- Format issues may break downstream integrations""",
        "summary": "Resolve data quality issues with AI recommendations",
        "category": "discovery",
        "flow_type": "discovery",
        "route": "/discovery/data-cleansing",
        "tags": ["cleansing", "quality", "duplicates", "missing", "validation"],
        "faq_questions": [
            "How do I fix duplicate records?",
            "What is the data quality score?",
            "Should I resolve all issues before proceeding?",
        ],
    },
    {
        "title": "Data Validation",
        "slug": "discovery-data-validation",
        "content": """Data Validation verifies your data meets business rules and quality standards
before proceeding to the Asset Inventory.

**Validation Checks:**
- Required field completeness
- Data format compliance
- Business rule validation
- Referential integrity
- Custom validation rules

**Validation Status:**
- **Passed**: All validations successful
- **Warnings**: Non-critical issues found
- **Failed**: Critical issues must be resolved

**How to Handle Failures:**
1. Review the validation error details
2. Navigate back to Data Cleansing to fix issues
3. Re-run validation after corrections
4. Override warnings if acceptable (with justification)

**Best Practices:**
- Address all critical failures before proceeding
- Document any warning overrides
- Run validation multiple times after bulk changes""",
        "summary": "Verify data meets business rules before proceeding",
        "category": "discovery",
        "flow_type": "discovery",
        "route": "/discovery/data-validation",
        "tags": ["validation", "rules", "quality", "checks", "compliance"],
        "faq_questions": [
            "Why is validation failing?",
            "Can I skip validation warnings?",
            "What are business rule validations?",
        ],
    },
]
