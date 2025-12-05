"""
General and cross-flow help content for contextual chat assistant.

Contains help articles for planning, decommission, finops, and troubleshooting.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

from typing import Any, Dict, List

# Planning, Decommission, FinOps, and General Help Content
GENERAL_CONTENT: List[Dict[str, Any]] = [
    # Planning Flow Help
    {
        "title": "Wave Planning Overview",
        "slug": "planning-wave-planning",
        "content": """Wave Planning organizes applications into migration groups called waves.

**What is Wave Planning?**
Waves are groups of applications migrated together based on:
- Dependencies between applications
- Resource availability
- Risk considerations
- Business priorities

**How to Create Waves:**
1. Review application list and dependencies
2. Drag applications into wave groups
3. Resolve dependency conflicts
4. Set wave timeline and resources
5. Validate and finalize wave plan

**Dependency Handling:**
- Applications with dependencies should migrate together
- Parent applications typically migrate first
- Circular dependencies require special planning

**Wave Timeline:**
- Set start and end dates for each wave
- Account for testing and validation time
- Include rollback windows
- Consider business calendar (avoid peak seasons)

**Best Practices:**
- Start with low-risk applications in Wave 1
- Group applications by business unit when possible
- Limit wave size to manageable scope
- Build in buffer time between waves""",
        "summary": "Organize applications into migration wave groups",
        "category": "planning",
        "flow_type": "planning",
        "route": "/plan/waveplanning",
        "tags": ["waves", "planning", "timeline", "dependencies", "groups"],
        "faq_questions": [
            "How do I create migration waves?",
            "What about application dependencies?",
            "How many applications per wave?",
        ],
    },
    # FinOps Help
    {
        "title": "Cloud Cost Comparison",
        "slug": "finops-cost-comparison",
        "content": """Compare cloud costs across AWS, Azure, and GCP to optimize your migration budget.

**Cost Categories:**
- **Compute**: Virtual machines, containers
- **Storage**: Block, object, file storage
- **Network**: Data transfer, load balancers
- **Database**: Managed database services
- **AI/ML**: Machine learning services

**How to Compare Costs:**
1. Select applications to analyze
2. Choose target cloud providers
3. Configure sizing and scaling
4. Review projected costs
5. Export comparison report

**LLM Cost Tracking:**
Track AI usage costs including:
- Token consumption by model
- Cost per analysis type
- Monthly trends and projections
- Cost optimization recommendations

**Optimization Strategies:**
- Right-size instances based on actual usage
- Use reserved instances for predictable workloads
- Leverage spot instances for batch processing
- Implement auto-scaling policies""",
        "summary": "Compare and optimize cloud provider costs",
        "category": "finops",
        "flow_type": "finops",
        "route": "/finops/comparison",
        "tags": ["cost", "cloud", "aws", "azure", "gcp", "optimization"],
        "faq_questions": [
            "Which cloud provider is cheapest?",
            "How are costs calculated?",
            "What is LLM cost tracking?",
        ],
    },
    # Decommission Help
    {
        "title": "Decommission Planning",
        "slug": "decommission-planning",
        "content": """Plan and track legacy system retirement with compliance and data preservation.

**Decommission Phases:**
1. **Planning**: Identify systems, assess impact
2. **Data Migration**: Move data to new systems
3. **System Shutdown**: Disable legacy systems
4. **Validation**: Verify successful decommission

**Key Considerations:**
- Data retention requirements
- Compliance and audit needs
- User notification and training
- Dependency removal
- License termination

**Compliance Checklist:**
- Document all data migrations
- Maintain audit trail
- Verify data integrity post-migration
- Archive historical records
- Update configuration management

**Best Practices:**
- Start with clear communication plan
- Test data migration in stages
- Maintain rollback capability
- Document lessons learned""",
        "summary": "Plan and execute legacy system decommissioning",
        "category": "decommission",
        "flow_type": "decommission",
        "route": "/decommission/planning",
        "tags": ["decommission", "retire", "legacy", "shutdown", "compliance"],
        "faq_questions": [
            "How do I decommission an application?",
            "What about data retention?",
            "How do I handle compliance requirements?",
        ],
    },
    # General/Troubleshooting Help
    {
        "title": "Common Troubleshooting",
        "slug": "troubleshooting-common",
        "content": """Solutions to common issues in the AI Force Assess platform.

**Data Import Issues:**
- **Upload fails**: Check file format (CSV/Excel), size (<50MB), and encoding (UTF-8)
- **Missing columns**: Ensure headers in first row
- **Parsing errors**: Remove special characters from headers

**Analysis Issues:**
- **Analysis stuck**: Refresh the page, check network connection
- **Low confidence scores**: Add more application data, answer qualifying questions
- **Unexpected recommendations**: Review parameter settings

**Performance Issues:**
- **Slow page load**: Clear browser cache, check network
- **Timeout errors**: Reduce data volume, try during off-peak hours
- **Session expired**: Re-login and continue from last saved state

**Browser Requirements:**
- Chrome (recommended), Firefox, Safari, or Edge
- JavaScript enabled
- Cookies enabled for session management
- Stable internet connection

**Getting Help:**
- Use the AI Chat Assistant for instant help
- Contact support for technical issues
- Check documentation for detailed guides""",
        "summary": "Solutions to common platform issues",
        "category": "troubleshooting",
        "flow_type": "general",
        "route": None,
        "tags": ["help", "troubleshooting", "errors", "issues", "support"],
        "faq_questions": [
            "Why is my upload failing?",
            "How do I fix analysis errors?",
            "What browsers are supported?",
        ],
    },
]
