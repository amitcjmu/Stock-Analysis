"""
Guided workflow prompts for contextual chat service.

Contains step-by-step guidance prompts based on current phase and pending actions.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

from typing import Dict

# Guided workflow prompts based on current phase and pending actions
GUIDED_WORKFLOW_PROMPTS: Dict[str, Dict[str, str]] = {
    "discovery": {
        "data_import": """
## Step-by-Step Guidance: Data Import
You're at the beginning of the Discovery flow. Here's what to do:

1. **Prepare Your Data File**
   - Use CSV or Excel format (.xlsx, .xls)
   - Include columns like: hostname, ip_address, os, environment, application
   - Ensure no sensitive credentials are in the file

2. **Upload the File**
   - Click or drag your file to the upload area
   - Wait for the AI to analyze the data
   - Review the preview to ensure data looks correct

3. **What Happens Next**
   After upload, the AI will automatically:
   - Analyze your columns and data types
   - Suggest field mappings to the standard schema
   - Identify potential data quality issues

**Common Issues:**
- File too large? Split into smaller batches
- Upload failing? Check file format (CSV/Excel only)
- Missing columns? That's OK - map them as "unmapped"
""",
        "field_mapping": """
## Step-by-Step Guidance: Field Mapping
Your data has been uploaded. Now let's map your columns to our standard schema.

1. **Review AI Suggestions**
   - Green (>80% confidence): Likely correct, approve in bulk
   - Yellow (50-80%): Review each suggestion carefully
   - Red (<50%): Manually select the correct mapping

2. **Map Required Fields**
   Priority fields for migration:
   - `hostname` or `server_name` → Asset Name
   - `ip_address` → IP Address
   - `os` or `operating_system` → Operating System
   - `environment` → Environment (Prod/Dev/Test)

3. **Approve Mappings**
   - Use "Approve All High Confidence" for green items
   - Review and fix yellow/red items manually
   - Click "Complete Mapping" when done

**Tips:**
- Not all columns need to be mapped
- You can come back and adjust mappings later
- AI learns from your corrections
""",
        "data_cleansing": """
## Step-by-Step Guidance: Data Cleansing
The AI has analyzed your data quality. Let's fix any issues found.

1. **Review Issue Types**
   - **Duplicates**: Same asset appears multiple times
   - **Missing Values**: Required fields are empty
   - **Invalid Formats**: Data doesn't match expected format
   - **Inconsistencies**: Values vary unexpectedly

2. **Resolve Issues**
   - For duplicates: Choose which record to keep
   - For missing values: Fill in or mark as unknown
   - For format issues: Accept AI suggestion or manually fix

3. **Use AI Recommendations**
   - The AI suggests fixes for most issues
   - Review suggestions before accepting
   - You can override any suggestion

**Priority Order:**
1. Fix critical issues (missing required fields)
2. Resolve duplicates
3. Fix format issues
4. Address inconsistencies
""",
        "data_validation": """
## Step-by-Step Guidance: Data Validation
Let's verify your data meets business rules before creating assets.

1. **Review Validation Rules**
   - Required fields are populated
   - Values are within expected ranges
   - References are valid (e.g., environment names)

2. **Address Validation Errors**
   - Critical errors must be fixed
   - Warnings can be reviewed and overridden
   - Info items are suggestions only

3. **Complete Validation**
   - All critical errors must be resolved
   - Review warnings for any needed action
   - Click "Validate" to proceed

**What Gets Validated:**
- Data completeness
- Format consistency
- Business rule compliance
- Cross-field dependencies
""",
        "asset_inventory": """
## Step-by-Step Guidance: Asset Inventory
Your data has been processed. Review your complete asset inventory.

1. **Review Created Assets**
   - Verify asset counts match your expectations
   - Check that key fields are populated
   - Look for any obviously wrong data

2. **Edit Individual Assets**
   - Click on an asset to view details
   - Make manual corrections if needed
   - Add notes or tags for organization

3. **Next Steps**
   From here you can:
   - Start **Collection** to gather more details
   - Begin **Assessment** to analyze migration strategies
   - Export data for reporting

**Discovery Complete!**
You've successfully imported and cleansed your asset data.
""",
    },
    "collection": {
        "gap_analysis": """
## Step-by-Step Guidance: Gap Analysis
The system is analyzing what additional information is needed.

1. **What's Being Analyzed**
   - Comparing your asset data against requirements
   - Identifying missing information per application
   - Prioritizing data gaps by importance

2. **Understanding Results**
   - Critical gaps: Must be filled before assessment
   - Important gaps: Recommended to fill
   - Optional gaps: Nice to have information

3. **What Happens Next**
   - AI will generate targeted questionnaires
   - Each application gets a personalized form
   - Questions adapt based on existing data
""",
        "questionnaire_generation": """
## Step-by-Step Guidance: Questionnaire Generation
AI is creating intelligent questionnaires based on your data gaps.

1. **How Questionnaires Work**
   - Each app gets a unique questionnaire
   - Questions are based on missing data
   - Answers from similar apps are suggested

2. **What to Expect**
   - Questions about architecture details
   - Technical specifications queries
   - Dependency information requests

3. **After Generation**
   - Review generated questionnaires
   - Assign to appropriate team members
   - Set deadlines if needed
""",
        "data_collection": """
## Step-by-Step Guidance: Data Collection
Time to fill in the questionnaires created for your applications.

1. **Answer Questions**
   - Use the adaptive form interface
   - Questions change based on your answers
   - AI suggests answers when possible

2. **Tips for Efficiency**
   - Start with applications you know best
   - Use bulk import for similar applications
   - Mark uncertain answers for review

3. **Track Progress**
   - Dashboard shows completion percentage
   - Prioritize critical questions first
   - All sections don't need to be completed at once
""",
    },
    "assessment": {
        "architecture_standards": """
## Step-by-Step Guidance: Architecture Standards
AI is analyzing your applications against cloud-ready architecture patterns.

1. **What's Being Analyzed**
   - Application architecture patterns
   - Technology stack compatibility
   - Cloud-native readiness

2. **Understanding Results**
   - Scores indicate cloud readiness
   - Recommendations suggest improvements
   - Gap analysis shows what's missing

3. **Review and Accept**
   - Check AI findings for accuracy
   - Add context where needed
   - Accept to proceed to next phase
""",
        "tech_debt_analysis": """
## Step-by-Step Guidance: Technical Debt Analysis
Identifying modernization needs for your applications.

1. **What's Being Assessed**
   - Legacy technology dependencies
   - Out-of-support components
   - Security vulnerabilities

2. **Understanding Debt Categories**
   - Critical: Must address before migration
   - High: Should address during migration
   - Medium/Low: Can address post-migration

3. **Action Items**
   - Review debt findings
   - Prioritize remediation
   - Factor into migration timeline
""",
        "dependency_analysis": """
## Step-by-Step Guidance: Dependency Analysis
Mapping relationships between your applications.

1. **What's Being Mapped**
   - Upstream dependencies (what this app needs)
   - Downstream dependencies (what needs this app)
   - Data flows between applications

2. **Review Dependency Graph**
   - Check detected relationships
   - Add missing dependencies
   - Correct any errors

3. **Impact on Migration**
   - Dependencies affect wave planning
   - Some apps must migrate together
   - Order matters for dependent apps
""",
        "6r_decision": """
## Step-by-Step Guidance: 6R Recommendations
Review AI-generated migration strategy recommendations.

1. **Understanding 6R Strategies**
   - **Rehost**: Lift-and-shift to cloud
   - **Replatform**: Minor optimizations
   - **Refactor**: Code changes for cloud
   - **Rearchitect**: Major redesign
   - **Rebuild**: Start fresh
   - **Retire**: Decommission

2. **Review Recommendations**
   - Check AI rationale for each app
   - Consider cost vs. effort tradeoffs
   - Factor in business priorities

3. **Accept or Modify**
   - Accept recommendations you agree with
   - Override with justification if needed
   - All apps need a decision to proceed
""",
    },
}
