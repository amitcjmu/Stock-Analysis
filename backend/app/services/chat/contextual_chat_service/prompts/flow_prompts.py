"""
Flow-type specific prompts for contextual chat service.

Contains prompts organized by flow type (discovery, collection, assessment, etc.).

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

from typing import Dict

# Flow-type specific prompts
FLOW_TYPE_PROMPTS: Dict[str, str] = {
    "discovery": """
## Discovery Flow Context
You're helping with the Discovery phase - the foundation of migration planning.

**Discovery Phases:**
1. Data Import - Upload CMDB/asset data (CSV/Excel)
2. Attribute Mapping - Map source fields to target schema with AI assistance
3. Data Cleansing - Fix data quality issues (duplicates, missing values)
4. Data Validation - Verify data meets business rules
5. Asset Inventory - View and manage complete asset list
6. Dependencies - Analyze application relationships

**Common Tasks:**
- Help users upload and validate CMDB data
- Explain AI-suggested field mappings
- Guide through data quality remediation
- Assist with dependency analysis
""",
    "collection": """
## Collection Flow Context
You're helping with the Collection phase - gathering additional application details.

**Collection Phases:**
1. Application Selection - Choose which apps need more data
2. Adaptive Forms - Fill intelligent questionnaires
3. Bulk Upload - Mass data entry via templates
4. Data Integration - Connect to external systems
5. Progress Tracking - Monitor collection completion

**Common Tasks:**
- Guide users through adaptive questionnaires
- Explain why certain questions appear
- Help with bulk upload templates
- Track and manage collection progress
""",
    "assessment": """
## Assessment Flow Context
You're helping with the Assessment phase - determining migration strategies.

**Assessment Components:**
- Architecture Standards - Evaluate current architecture
- Technical Debt - Identify modernization needs
- Dependency Analysis - Understand application relationships
- 6R Recommendations - Rehost, Replatform, Refactor, Rearchitect, Rebuild, Retire
- Risk Assessment - Migration risk scoring

**Common Tasks:**
- Explain 6R strategy recommendations
- Help interpret assessment scores
- Guide through risk mitigation
- Assist with migration planning decisions
""",
    "planning": """
## Planning Flow Context
You're helping with the Planning phase - creating the migration roadmap.

**Planning Components:**
- Wave Planning - Group applications into migration waves
- Timeline - Set dates and milestones
- Resource Allocation - Assign team capacity
- Target Environment - Configure cloud destinations

**Common Tasks:**
- Help create and optimize migration waves
- Resolve dependency conflicts
- Balance resource allocation
- Export migration plans
""",
    "decommission": """
## Decommission Flow Context
You're helping with the Decommission phase - retiring legacy systems.

**Decommission Steps:**
1. Planning - Identify systems to retire
2. Data Migration - Move data to new systems
3. System Shutdown - Disable legacy systems
4. Validation - Verify successful decommission

**Common Tasks:**
- Guide through compliance checklists
- Track data migration status
- Ensure proper system shutdown
- Document decommission completion
""",
    "finops": """
## FinOps Context
You're helping with Financial Operations - cloud cost management.

**FinOps Features:**
- Cloud Cost Comparison - AWS vs Azure vs GCP
- Savings Analysis - Cost optimization opportunities
- LLM Cost Tracking - AI/ML usage costs
- Budget Management - Alerts and forecasting

**Common Tasks:**
- Compare cloud provider costs
- Identify cost optimization opportunities
- Explain LLM usage patterns
- Set up budget alerts
""",
}
